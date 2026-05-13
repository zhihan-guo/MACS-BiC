"""
MACS-BiC Multi-Agent System.

Five agents:
    - PlannerAgent       : turns a user domain into a research plan (GPT-4o).
    - CoordinatorAgent   : orchestrates the pipeline and aligns I/O between agents.
    - PaperReaderAgent   : extracts Q&A JSONL per paper.
    - DataWriterAgent    : merges JSONL into the final Excel.
    - JudgerAgent        : validates accuracy/format; triggers re-runs.

Six tools (all under ``multi_agent/tools/``):
    retrieval_search, paper_download, paper_parsing, image_to_text,
    carbon_footprint_calculating, dataset_construction.

Typical entry-point usage::

    mas = MultiAgentSystem(api_key="sk-...", wos_api_key="...", gemini_api_key="...")
    result = mas.run(domain="biochar concrete carbon footprint", workspace="./run_001")
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .llm_client import LLMClient
from .agents import (
    PlannerAgent,
    CoordinatorAgent,
    PaperReaderAgent,
    DataWriterAgent,
    JudgerAgent,
)


class MultiAgentSystem:
    """Top-level façade for the five-agent / six-tool pipeline."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://az.gptplus5.com/v1",
        model_name: str = "gpt-4o-2024-11-20",
        extraction_model: Optional[str] = None,
        *,
        llm_client: Optional[LLMClient] = None,
        wos_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        use_llm_judge: bool = True,
    ) -> None:
        if llm_client is None:
            if not api_key:
                api_key = os.environ.get("OPENAI_API_KEY", "")
            llm_client = LLMClient(api_key=api_key, model_name=model_name, base_url=base_url)
        self.llm_client = llm_client

        self.planner = PlannerAgent(llm_client=self.llm_client)
        self.paper_reader = PaperReaderAgent(llm_client=self.llm_client)
        self.data_writer = DataWriterAgent(llm_client=self.llm_client)
        self.judger = JudgerAgent(llm_client=self.llm_client, use_llm_check=use_llm_judge)
        self.coordinator = CoordinatorAgent(
            llm_client=self.llm_client,
            paper_reader=self.paper_reader,
            data_writer=self.data_writer,
            judger=self.judger,
            extraction_model=extraction_model or model_name,
            wos_api_key=wos_api_key or os.environ.get("WOS_API_KEY"),
            gemini_api_key=gemini_api_key or os.environ.get("GEMINI_API_KEY"),
        )

        self.agents = {
            "planner": self.planner,
            "coordinator": self.coordinator,
            "paper_reader": self.paper_reader,
            "data_writer": self.data_writer,
            "judger": self.judger,
        }

    def run(self, domain: str, workspace: str, *, max_records: int = 100) -> Dict[str, Any]:
        """
        Execute the full pipeline for the given research domain.

        Steps:
            1. Planner generates a structured plan.
            2. Coordinator runs retrieval -> download -> parsing -> extraction
               -> judging -> dataset assembly.

        Parameters
        ----------
        domain : str
            User-supplied research domain (free text).
        workspace : str
            Root folder for every intermediate artefact.
        max_records : int
            Upper bound on the number of DOIs fetched from WoS.
        """
        planner_result = self.planner.execute_task(
            f"Build a research plan for the following domain: {domain!r}. "
            f"Workspace: {workspace!r}. Target dataset format: Excel. "
            "Reply by calling `submit_plan` with the JSON plan, then `task_done`."
        )
        plan = self.planner.plan
        if not plan:
            return {
                "success": False,
                "stage": "planner",
                "error": "Planner did not produce a valid plan.",
                "planner_result": planner_result,
            }

        coord_brief = (
            "Execute the following research plan end-to-end. "
            "Drive the pipeline with the tools in this exact order: "
            "init_workspace, run_retrieval, run_download, run_parsing, "
            "run_extraction_batch, run_judging_batch, build_dataset. "
            "Then call task_done with a one-paragraph summary.\n\n"
            f"PLAN_JSON = {json.dumps(plan, ensure_ascii=False)}\n"
            f"WORKSPACE = {workspace!r}\n"
            f"MAX_RECORDS = {max_records}\n"
        )
        coord_result = self.coordinator.execute_task(coord_brief)

        return {
            "success": coord_result.get("success", False),
            "plan": plan,
            "planner_result": planner_result,
            "coordinator_result": coord_result,
            "context": self.coordinator.context,
        }

    def run_programmatic(
        self,
        domain: str,
        workspace: str,
        *,
        max_records: int = 100,
        backend: str = "pipeline",
        required_questions: Optional[list] = None,
        drop_columns: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic, LLM-free path through the pipeline (handy for tests / CI).

        Runs the same stages as :meth:`run` but calls the coordinator's tool
        methods directly instead of going through the ReAct loop.
        """
        planner_result = self.planner.execute_task(
            f"Build a research plan for the domain: {domain!r}. "
            "Reply by calling `submit_plan` then `task_done`."
        )
        plan = self.planner.plan or {
            "domain": domain,
            "keywords": [domain],
            "questions": ["1.1", "2.5"],
            "tools": [
                "retrieval_search", "paper_download", "paper_parsing",
                "image_to_text", "carbon_footprint_calculating", "dataset_construction",
            ],
            "agents": ["paper_reader", "data_writer", "judger"],
            "success_criteria": {"min_papers": 1, "format": "excel"},
            "notes": "Fallback plan (LLM unavailable).",
        }

        steps = {}
        steps["init"] = self.coordinator.init_workspace(plan_json=json.dumps(plan), workspace=workspace)
        steps["retrieval"] = self.coordinator.run_retrieval(max_records=max_records)
        steps["download"] = self.coordinator.run_download()
        steps["parsing"] = self.coordinator.run_parsing(backend=backend)
        steps["extraction"] = self.coordinator.run_extraction_batch()
        steps["judging"] = self.coordinator.run_judging_batch(required_questions=required_questions)
        steps["dataset"] = self.coordinator.build_dataset(drop_columns=drop_columns)

        return {
            "success": all(s.get("success", False) for s in steps.values()),
            "plan": plan,
            "planner_result": planner_result,
            "steps": steps,
            "context": self.coordinator.context,
        }

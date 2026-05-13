"""
Coordinator agent.

Owns the canonical inter-agent message schema and drives the whole pipeline.

Pipeline (executed in order):

    1. retrieval_search        - find DOIs in WoS for the planner's keywords
    2. paper_download          - download PDFs for those DOIs
    3. paper_parsing           - convert PDFs to markdown + figures (MinerU)
    4. paper_reader (loop)     - extract Q&A JSONL per paper using image_to_text
    5. judger (per paper)      - validate accuracy/format; retry once on fail
    6. dataset_construction    - merge JSONL files into the final Excel
    7. (optional) carbon_footprint_calculating per row

The coordinator exposes one *tool per pipeline stage* to the LLM. A typical
GPT-4o trace looks like::

    init_workspace -> run_retrieval -> run_download -> run_parsing
        -> run_extraction_batch -> run_judging_batch -> build_dataset
        -> compute_carbon_footprint -> task_done

The agent keeps an internal ``context`` dict that flows between calls so each
tool only needs to receive the *delta* it actually owns.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from ..base_agent import ReActBaseAgent
from ..llm_client import LLMClient
from ..mcp_tool import mcp_tool

from ..tools.retrieval import retrieval_search
from ..tools.paper_download import paper_download
from ..tools.paper_parsing import paper_parsing
from ..tools.image_to_text import image_to_text
from ..tools.carbon_footprint import carbon_footprint_calculating
from ..tools.dataset_construction import dataset_construction

from .paper_reader import PaperReaderAgent
from .data_writer import DataWriterAgent
from .judger import JudgerAgent


COORDINATOR_SYSTEM_PROMPT = (
    "You are the Coordinator agent of the MACS-BiC multi-agent system.\n"
    "You receive a research plan (JSON) produced by the Planner. Drive the "
    "end-to-end paper-mining pipeline by calling the tools below IN ORDER:\n"
    "  1. `init_workspace`   - prepare on-disk folders.\n"
    "  2. `run_retrieval`    - get DOIs from WoS.\n"
    "  3. `run_download`     - download the PDFs.\n"
    "  4. `run_parsing`      - parse PDFs via MinerU.\n"
    "  5. `run_extraction_batch` - have the Paper Reader extract every paper.\n"
    "  6. `run_judging_batch` - have the Judger validate; auto-retry on fail.\n"
    "  7. `build_dataset`    - have the Data Writer produce the Excel.\n"
    "  8. (optional) `compute_carbon_footprint` for each row.\n"
    "  9. `task_done` with a final summary.\n"
    "The canonical inter-agent message format is:\n"
    "  {\"from\": agent_id, \"to\": agent_id, \"stage\": stage_name, "
    "\"payload\": {...}, \"meta\": {...}}\n"
    "When a stage fails, surface the error in the summary; do NOT skip stages."
)


class CoordinatorAgent(ReActBaseAgent):
    """Plan executor that delegates to Paper Reader / Data Writer / Judger."""

    def __init__(
        self,
        llm_client: LLMClient,
        paper_reader: PaperReaderAgent,
        data_writer: DataWriterAgent,
        judger: JudgerAgent,
        *,
        extraction_model: str = "gpt-4o-2024-11-20",
        wos_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ) -> None:
        super().__init__(llm_client=llm_client, system_prompt=COORDINATOR_SYSTEM_PROMPT)
        self.max_iterations = 30
        self.paper_reader = paper_reader
        self.data_writer = data_writer
        self.judger = judger
        self.extraction_model = extraction_model
        self.wos_api_key = wos_api_key
        self.gemini_api_key = gemini_api_key
        self.context: Dict[str, Any] = {
            "plan": {},
            "workspace": {},
            "dois": [],
            "pdfs": [],
            "parsed": [],
            "extractions": [],
            "judgments": [],
            "dataset": None,
        }

    @staticmethod
    def make_message(
        sender: str,
        receiver: str,
        stage: str,
        payload: Dict[str, Any],
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Canonical inter-agent envelope produced by the Coordinator."""
        return {
            "from": sender,
            "to": receiver,
            "stage": stage,
            "payload": payload,
            "meta": meta or {},
        }

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "plan_json": {"type": "string", "description": "Research plan JSON produced by the Planner."},
                "workspace": {"type": "string", "description": "Root directory for all intermediate artefacts."},
            },
            "required": ["plan_json", "workspace"],
        },
        description="Store the research plan, create workspace sub-folders, and return the resolved paths.",
    )
    def init_workspace(self, plan_json: str, workspace: str) -> Dict[str, Any]:
        try:
            plan = json.loads(plan_json) if isinstance(plan_json, str) else plan_json
        except json.JSONDecodeError as exc:
            return {"success": False, "error": f"Invalid plan JSON: {exc}"}

        workspace = os.path.abspath(workspace)
        sub = {
            "pdfs": os.path.join(workspace, "pdfs"),
            "parsed": os.path.join(workspace, "parsed"),
            "image_text": os.path.join(workspace, "image_text"),
            "results1": os.path.join(workspace, "results1"),
            "extractions": os.path.join(workspace, "extractions"),
            "excel": os.path.join(workspace, "dataset.xlsx"),
        }
        for k, p in sub.items():
            if k != "excel":
                os.makedirs(p, exist_ok=True)

        self.context["plan"] = plan
        self.context["workspace"] = {"root": workspace, **sub}
        return {"success": True, "data": self.context["workspace"]}

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "max_records": {"type": "integer", "description": "Upper bound of DOIs to fetch."},
            },
        },
        description="Run the retrieval tool using the plan's domain + keywords.",
    )
    def run_retrieval(self, max_records: int = 200) -> Dict[str, Any]:
        plan = self.context.get("plan") or {}
        result = retrieval_search(
            domain=plan.get("domain", ""),
            keywords=plan.get("keywords") or [],
            api_key=self.wos_api_key,
            max_records=max_records,
        )
        if not result.get("success"):
            return result
        dois = result["data"]["dois"]
        self.context["dois"] = dois
        return {"success": True, "data": {"count": len(dois), "sample": dois[:5]}}

    @mcp_tool(
        input_schema={"type": "object", "properties": {}},
        description="Download PDFs for every DOI gathered by `run_retrieval`.",
    )
    def run_download(self) -> Dict[str, Any]:
        ws = self.context["workspace"]
        result = paper_download(
            dois=self.context["dois"],
            output_dir=ws["pdfs"],
            api_key=self.wos_api_key,
        )
        if not result.get("success"):
            return result
        self.context["pdfs"] = [d["path"] for d in result["data"]["downloaded"]]
        return {
            "success": True,
            "data": {
                "downloaded": len(result["data"]["downloaded"]),
                "failed": len(result["data"]["failed"]),
            },
        }

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "backend": {
                    "type": "string",
                    "description": "MinerU backend: 'pipeline' (default), 'vlm-transformers', or 'vlm-vllm-engine'.",
                }
            },
        },
        description="Convert all downloaded PDFs to markdown + figure images using MinerU.",
    )
    def run_parsing(self, backend: str = "pipeline") -> Dict[str, Any]:
        ws = self.context["workspace"]
        result = paper_parsing(
            pdf_paths=self.context["pdfs"],
            output_dir=ws["parsed"],
            backend=backend,
        )
        if not result.get("success"):
            return result
        self.context["parsed"] = result["data"]["parsed"]
        return {
            "success": True,
            "data": {
                "parsed": len(result["data"]["parsed"]),
                "failed": len(result["data"]["failed"]),
            },
        }

    @mcp_tool(
        input_schema={"type": "object", "properties": {}},
        description=(
            "Run the Paper Reader on every successfully parsed paper. "
            "Caches Gemini image-to-text translations and produces one JSONL per DOI."
        ),
    )
    def run_extraction_batch(self) -> Dict[str, Any]:
        ws = self.context["workspace"]
        extractions: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []

        for parsed in self.context["parsed"]:
            doi = self._doi_from_pdf(parsed["pdf"])

            img_res = image_to_text(
                doi=doi,
                images_dir=parsed["images"],
                output_dir=ws["image_text"],
                api_key=self.gemini_api_key,
            )
            if not img_res.get("success"):
                failures.append({"doi": doi, "stage": "image_to_text", "error": img_res.get("error")})
                continue

            envelope = self.make_message(
                sender="coordinator",
                receiver="paper_reader",
                stage="extraction",
                payload={
                    "doi": doi,
                    "pdf": parsed["pdf"],
                    "markdown": parsed["markdown"],
                    "images_dir": parsed["images"],
                    "output_dir": ws["extractions"],
                    "image_text_dir": ws["image_text"],
                    "results1_dir": ws["results1"],
                    "model": self.extraction_model,
                },
            )
            reader_result = self.paper_reader.extract_paper(**envelope["payload"])
            if reader_result.get("success"):
                extractions.append(reader_result["data"])
            else:
                failures.append({"doi": doi, "stage": "paper_reader", "error": reader_result.get("error")})

        self.context["extractions"] = extractions
        return {
            "success": True,
            "data": {
                "extracted": len(extractions),
                "failed": len(failures),
                "failures": failures,
            },
        }

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "required_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Question IDs the Judger requires to be non-empty.",
                },
                "max_retries": {"type": "integer", "description": "How many times to re-run the Paper Reader on failure (default 1)."},
            },
        },
        description="Validate every JSONL extraction with the Judger; retry the Paper Reader on failures.",
    )
    def run_judging_batch(
        self,
        required_questions: Optional[List[str]] = None,
        max_retries: int = 1,
    ) -> Dict[str, Any]:
        judgments: List[Dict[str, Any]] = []
        for extraction in list(self.context["extractions"]):
            verdict = self._judge_one(extraction, required_questions)
            attempts = 0
            while verdict.get("retry") and attempts < max_retries:
                attempts += 1
                rerun = self._rerun_extraction(extraction["doi"])
                if rerun:
                    extraction = rerun
                verdict = self._judge_one(extraction, required_questions)
            judgments.append({"doi": extraction.get("doi"), "verdict": verdict, "attempts": attempts})

        self.context["judgments"] = judgments
        passed = sum(1 for j in judgments if j["verdict"].get("verdict") == "pass")
        return {
            "success": True,
            "data": {"total": len(judgments), "passed": passed, "failed": len(judgments) - passed},
        }

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "drop_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to drop (e.g. ['text', 'table_and_charts']).",
                },
                "include_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional whitelist of columns to keep.",
                },
            },
        },
        description="Use the Data Writer to merge every JSONL extraction into the final Excel workbook.",
    )
    def build_dataset(
        self,
        drop_columns: Optional[List[str]] = None,
        include_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        ws = self.context["workspace"]
        result = self.data_writer.write_excel(
            input_dir=ws["extractions"],
            output_excel=ws["excel"],
            drop_columns=drop_columns,
            include_columns=include_columns,
        )
        if result.get("success"):
            self.context["dataset"] = result["data"]
        return result

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "mixtures": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of mixtures, each a mapping of component (or question id like '2.5') -> mass ratio.",
                },
                "custom_factors": {
                    "type": "object",
                    "description": "Optional override of emission factors (component name -> kg CO2 per unit).",
                },
            },
            "required": ["mixtures"],
        },
        description="Compute the LCA carbon footprint f(cf) = sum_k(m_k * Cef_k) for a list of mixtures.",
    )
    def compute_carbon_footprint(
        self,
        mixtures: List[Dict[str, Any]],
        custom_factors: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        results = [carbon_footprint_calculating(m, custom_factors=custom_factors) for m in mixtures]
        return {"success": True, "data": {"count": len(results), "results": results}}

    def _judge_one(self, extraction: Dict[str, Any], required_questions: Optional[List[str]]) -> Dict[str, Any]:
        jsonl = extraction.get("jsonl")
        if not jsonl:
            return {"verdict": "fail", "issues": ["No JSONL path in extraction"], "retry": False}
        result = self.judger.judge_extraction(jsonl_path=jsonl, required_questions=required_questions)
        return result.get("data", {})

    def _rerun_extraction(self, doi: str) -> Optional[Dict[str, Any]]:
        ws = self.context["workspace"]
        parsed = next((p for p in self.context["parsed"] if self._doi_from_pdf(p["pdf"]) == doi), None)
        if not parsed:
            return None

        safe = doi.replace("/", "_")
        stale = os.path.join(ws["extractions"], f"{safe}.jsonl")
        if os.path.exists(stale):
            try:
                os.remove(stale)
            except OSError:
                pass

        reader_result = self.paper_reader.extract_paper(
            doi=doi,
            pdf=parsed["pdf"],
            markdown=parsed["markdown"],
            images_dir=parsed["images"],
            output_dir=ws["extractions"],
            image_text_dir=ws["image_text"],
            results1_dir=ws["results1"],
            model=self.extraction_model,
        )
        if reader_result.get("success"):
            return reader_result["data"]
        return None

    @staticmethod
    def _doi_from_pdf(pdf_path: str) -> str:
        stem = os.path.splitext(os.path.basename(pdf_path))[0]
        return stem

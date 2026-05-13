"""
Planner agent.

Receives the user-supplied research domain (free text) and produces a JSON
research plan that the coordinator can execute.  Powered by GPT-4o.

The plan schema is intentionally simple and machine-readable so the
``CoordinatorAgent`` can rely on every field being present::

    {
        "domain": "...",
        "keywords": ["...", "..."],
        "questions": ["...", "..."],
        "tools": ["retrieval_search", "paper_download", ...],
        "agents": ["paper_reader", "data_writer", "judger"],
        "success_criteria": {
            "min_papers": int,
            "required_fields": ["doi", "qa", "success"],
            "format": "excel"
        },
        "notes": "..."
    }
"""

from __future__ import annotations

import json
from typing import Any, Dict

from ..base_agent import ReActBaseAgent
from ..llm_client import LLMClient
from ..mcp_tool import mcp_tool


PLANNER_SYSTEM_PROMPT = (
    "You are the Planner agent of the MACS-BiC multi-agent system.\n"
    "Your job is to translate a user-supplied research domain into a concise "
    "JSON research plan that downstream agents can execute. The plan MUST be a "
    "single JSON object with these keys:\n"
    "  - domain (string)\n"
    "  - keywords (list of strings; 3-8 keywords useful for WoS topic search)\n"
    "  - questions (list of strings; the extraction questions to ask each paper)\n"
    "  - tools (list of strings; subset of [retrieval_search, paper_download, "
    "paper_parsing, image_to_text, carbon_footprint_calculating, dataset_construction])\n"
    "  - agents (list of strings; subset of [paper_reader, data_writer, judger])\n"
    "  - success_criteria (object; at minimum {min_papers:int, format:'excel'})\n"
    "  - notes (string; short rationale for the plan)\n"
    "Workflow:\n"
    "  1. Reason briefly about the domain.\n"
    "  2. Build the JSON plan as described above.\n"
    "  3. Call the `submit_plan` tool with the JSON string.\n"
    "  4. When `submit_plan` returns success, call `task_done` with a 1-line summary.\n"
    "Never invent tools or agents that are not in the allowed lists."
)


class PlannerAgent(ReActBaseAgent):
    """Generate a structured research plan from the user's domain prompt."""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client=llm_client, system_prompt=PLANNER_SYSTEM_PROMPT)
        self.max_iterations = 6
        self._plan: Dict[str, Any] = {}

    @property
    def plan(self) -> Dict[str, Any]:
        return self._plan

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "plan_json": {
                    "type": "string",
                    "description": "The full research plan as a JSON string conforming to the schema in the system prompt.",
                }
            },
            "required": ["plan_json"],
        },
        description="Submit the final research plan as a JSON string. Returns success after validation.",
    )
    def submit_plan(self, plan_json: str) -> Dict[str, Any]:
        try:
            plan = json.loads(plan_json)
        except json.JSONDecodeError as exc:
            return {"success": False, "error": f"Invalid JSON: {exc}"}

        required = {"domain", "keywords", "questions", "tools", "agents", "success_criteria"}
        missing = required - set(plan.keys())
        if missing:
            return {"success": False, "error": f"Missing required keys: {sorted(missing)}"}

        if not isinstance(plan["keywords"], list) or not plan["keywords"]:
            return {"success": False, "error": "`keywords` must be a non-empty list."}
        if not isinstance(plan["questions"], list) or not plan["questions"]:
            return {"success": False, "error": "`questions` must be a non-empty list."}

        self._plan = plan
        return {"success": True, "data": plan}

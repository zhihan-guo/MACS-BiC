"""
Judger agent.

Validates the Paper Reader output for a single paper.

Two layers of validation:

1. **Programmatic checks** (always run): every record has the required keys,
   the ``qa`` mapping is a non-empty dict, ``success`` is True, and a minimum
   set of mandatory questions are non-empty / non-"nan".

2. **LLM check** (optional, when an LLM client is available): we ask GPT-4o
   to score the extraction for *accuracy* (does the answer make sense given
   the question prompt) and *format* (is the answer in the expected shape).
   The model returns ``{"verdict": "pass"|"fail", "issues": [...]}`` which is
   then merged with the programmatic verdict.

If the verdict is ``fail``, the agent returns ``retry=True`` so the
Coordinator can re-run the Paper Reader.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from ..base_agent import ReActBaseAgent
from ..llm_client import LLMClient
from ..mcp_tool import mcp_tool


JUDGER_SYSTEM_PROMPT = (
    "You are the Judger agent of the MACS-BiC multi-agent system.\n"
    "For every JSONL record produced by the Paper Reader you must:\n"
    "  1. Call `judge_extraction` with the JSONL path and the list of "
    "mandatory questions.\n"
    "  2. Once the verdict is available, summarise with `task_done`. The "
    "summary MUST include `pass` or `fail` and, when failing, the reason "
    "and `retry=true` so the Coordinator can re-run the Paper Reader."
)


MANDATORY_TOP_LEVEL_FIELDS = ("doi", "pdf", "qa", "success")


class JudgerAgent(ReActBaseAgent):
    """Validate a paper's JSONL extraction; trigger retries when needed."""

    def __init__(
        self,
        llm_client: LLMClient,
        *,
        use_llm_check: bool = True,
    ) -> None:
        super().__init__(llm_client=llm_client, system_prompt=JUDGER_SYSTEM_PROMPT)
        self.max_iterations = 4
        self.use_llm_check = use_llm_check

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "jsonl_path": {"type": "string", "description": "Path to the JSONL produced by the Paper Reader."},
                "required_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of question IDs / prefixes that must have a non-empty answer (e.g. ['1.1', '2.5']).",
                },
                "use_llm": {
                    "type": "boolean",
                    "description": "If true (default) and an LLM client is configured, also run an LLM-based accuracy check.",
                },
            },
            "required": ["jsonl_path"],
        },
        description="Check accuracy and format of a paper extraction. Returns verdict, issues, and retry hint.",
    )
    def judge_extraction(
        self,
        jsonl_path: str,
        required_questions: Optional[List[str]] = None,
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        if not os.path.exists(jsonl_path):
            return {
                "success": True,
                "data": {"verdict": "fail", "issues": [f"JSONL not found: {jsonl_path}"], "retry": True},
            }

        records: List[Dict[str, Any]] = []
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except Exception as exc:
            return {
                "success": True,
                "data": {"verdict": "fail", "issues": [f"Failed to parse JSONL: {exc}"], "retry": True},
            }

        if not records:
            return {
                "success": True,
                "data": {"verdict": "fail", "issues": ["Empty JSONL"], "retry": True},
            }

        issues: List[str] = []
        for idx, rec in enumerate(records):
            for k in MANDATORY_TOP_LEVEL_FIELDS:
                if k not in rec:
                    issues.append(f"record[{idx}]: missing field `{k}`")
            qa = rec.get("qa")
            if not isinstance(qa, dict) or not qa:
                issues.append(f"record[{idx}]: `qa` must be a non-empty dict")
            elif required_questions:
                for q in required_questions:
                    matching = [v for k, v in qa.items() if k.startswith(q)]
                    if not matching or all((v is None or str(v).strip().lower() in {"", "nan"}) for v in matching):
                        issues.append(f"record[{idx}]: required question `{q}` has no usable answer")
            if rec.get("success") is False:
                issues.append(f"record[{idx}]: extraction was marked `success=false`")

        llm_issues: List[str] = []
        if use_llm and self.use_llm_check:
            llm_issues = self._llm_check(records[0])
            issues.extend(llm_issues)

        verdict = "pass" if not issues else "fail"
        return {
            "success": True,
            "data": {
                "verdict": verdict,
                "issues": issues,
                "retry": verdict == "fail",
                "record_count": len(records),
                "jsonl_path": jsonl_path,
            },
        }

    def _llm_check(self, record: Dict[str, Any]) -> List[str]:
        """Run a single GPT-4o sanity check on the Q&A mapping."""
        try:
            sample = {
                "doi": record.get("doi"),
                "qa": record.get("qa"),
                "success": record.get("success"),
            }
            prompt = (
                "You are an LCA / construction-materials reviewer. The JSON below is the structured "
                "extraction of one paper performed by an LLM agent. Check ONLY for obvious accuracy "
                "or format problems (impossible values, off-topic answers, wrong units, malformed "
                "ratios). Reply with a JSON object of the form {\"verdict\": \"pass\"|\"fail\", "
                "\"issues\": [\"...\"]}. Do not invent issues.\n\n"
                f"Extraction:\n{json.dumps(sample, ensure_ascii=False)[:8000]}"
            )
            msg = [
                {"role": "system", "content": "Return ONLY a valid JSON object as instructed."},
                {"role": "user", "content": prompt},
            ]
            response = self.llm.generate(hist_messages=msg, tools=None)
            content = (response.content or "").strip()
            if content.startswith("```"):
                content = content.strip("`")
                if "\n" in content:
                    content = content.split("\n", 1)[1]
            parsed = json.loads(content)
            if parsed.get("verdict") == "fail":
                return [f"llm: {i}" for i in parsed.get("issues") or []] or ["llm: failed without details"]
            return []
        except Exception:
            return []

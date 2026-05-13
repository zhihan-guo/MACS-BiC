"""
Paper Reader agent.

Given a paper's PDF, the corresponding MinerU-parsed markdown, and the
Gemini-translated description of the figures/tables, this agent asks GPT-4o
the preset extraction questions and writes the answers as a JSONL record.

The agent re-uses the production extraction utilities that already live in
``agent/utils/utils.py`` so the JSONL format remains identical to what the
existing pipeline produces.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

from ..base_agent import ReActBaseAgent
from ..llm_client import LLMClient
from ..mcp_tool import mcp_tool


READER_SYSTEM_PROMPT = (
    "You are the Paper Reader agent of the MACS-BiC multi-agent system.\n"
    "For each paper assigned by the Coordinator you must:\n"
    "  1. Call the `extract_paper` tool with the full paper context "
    "(doi, pdf path, markdown path, images folder, output folder, image-cache "
    "folder, results-1 cache folder, model name).\n"
    "  2. When `extract_paper` returns success, call `task_done` with a 1-line "
    "summary that includes the DOI and the JSONL output path.\n"
    "If `extract_paper` fails, retry once with the same arguments. If it still "
    "fails, mark the task done with success=false and report the error."
)


def _ensure_utils_on_path() -> None:
    """Add ``agent/`` to ``sys.path`` so we can import the legacy extraction utils."""
    here = os.path.dirname(os.path.abspath(__file__))
    agent_root = os.path.normpath(os.path.join(here, "..", "..", ".."))
    if agent_root not in sys.path:
        sys.path.insert(0, agent_root)
    agent_dir = os.path.normpath(os.path.join(here, "..", ".."))
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)


class PaperReaderAgent(ReActBaseAgent):
    """Run the per-paper extraction loop and write a JSONL record."""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client=llm_client, system_prompt=READER_SYSTEM_PROMPT)
        self.max_iterations = 6

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "doi": {"type": "string", "description": "DOI of the paper."},
                "pdf": {"type": "string", "description": "Absolute path to the paper PDF."},
                "markdown": {"type": "string", "description": "MinerU-produced markdown file."},
                "images_dir": {"type": "string", "description": "MinerU-produced images folder."},
                "output_dir": {"type": "string", "description": "Folder where the JSONL Q&A record will be written."},
                "image_text_dir": {"type": "string", "description": "Folder caching the Gemini image-to-text translations."},
                "results1_dir": {"type": "string", "description": "Folder caching the prompt-1 results."},
                "model": {"type": "string", "description": "OpenAI model used for extraction (e.g. gpt-4o-2024-11-20)."},
            },
            "required": ["doi", "pdf", "markdown", "images_dir", "output_dir", "image_text_dir", "results1_dir", "model"],
        },
        description="Extract structured Q&A from one paper and append the result to a JSONL file. "
                    "Re-uses the production utilities in `agent/utils/utils.py`.",
    )
    def extract_paper(
        self,
        doi: str,
        pdf: str,
        markdown: str,
        images_dir: str,
        output_dir: str,
        image_text_dir: str,
        results1_dir: str,
        model: str,
    ) -> Dict[str, Any]:
        _ensure_utils_on_path()
        try:
            from utils.utils import (
                get_question_biochar_multi_pdf_process_data,
            )
        except Exception as exc:
            return {"success": False, "error": f"Failed to import extraction utilities: {exc}"}

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(image_text_dir, exist_ok=True)
        os.makedirs(results1_dir, exist_ok=True)

        data = {
            "doi": doi,
            "pdf": pdf,
            "markdown": markdown,
            "images": images_dir,
        }
        try:
            get_question_biochar_multi_pdf_process_data(
                data=data,
                model=model,
                output_path=output_dir,
                image_output_path=image_text_dir,
                result1=results1_dir,
            )
        except Exception as exc:
            return {"success": False, "error": f"extraction failed: {exc}"}

        safe = doi.replace("/", "_")
        jsonl_path = os.path.join(output_dir, f"{safe}.jsonl")
        if not os.path.exists(jsonl_path):
            return {"success": False, "error": f"Expected JSONL output {jsonl_path} was not produced."}

        records = []
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except Exception:
            pass

        return {
            "success": True,
            "data": {
                "doi": doi,
                "jsonl": jsonl_path,
                "record_count": len(records),
                "first_record_preview": records[0] if records else None,
            },
        }

    def read_paper(
        self,
        doi: str,
        pdf: str,
        markdown: str,
        images_dir: str,
        output_dir: str,
        image_text_dir: str,
        results1_dir: str,
        model: str = "gpt-4o-2024-11-20",
    ) -> Dict[str, Any]:
        """Imperative helper that bypasses the ReAct loop (useful for testing)."""
        return self.extract_paper(
            doi=doi,
            pdf=pdf,
            markdown=markdown,
            images_dir=images_dir,
            output_dir=output_dir,
            image_text_dir=image_text_dir,
            results1_dir=results1_dir,
            model=model,
        )

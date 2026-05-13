"""
Data Writer agent.

Reads every per-paper JSONL produced by the Paper Reader, flattens the Q&A
mapping and writes the merged dataset to an Excel workbook.  The heavy lifting
is delegated to ``tools/dataset_construction.py`` which is identical in spirit
to the legacy implementation in ``agent/utils/utils.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..base_agent import ReActBaseAgent
from ..llm_client import LLMClient
from ..mcp_tool import mcp_tool
from ..tools.dataset_construction import dataset_construction


WRITER_SYSTEM_PROMPT = (
    "You are the Data Writer agent of the MACS-BiC multi-agent system.\n"
    "When the Coordinator asks you to produce the final dataset, call the "
    "`write_excel` tool with the JSONL input folder and the desired output "
    ".xlsx path. Once it returns success, summarise with `task_done`."
)


class DataWriterAgent(ReActBaseAgent):
    """Combine per-paper JSONL records into a final Excel dataset."""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client=llm_client, system_prompt=WRITER_SYSTEM_PROMPT)
        self.max_iterations = 4

    @mcp_tool(
        input_schema={
            "type": "object",
            "properties": {
                "input_dir": {"type": "string", "description": "Folder containing per-DOI JSONL files."},
                "output_excel": {"type": "string", "description": "Destination .xlsx file path."},
                "drop_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to drop from the spreadsheet (e.g. ['text', 'table_and_charts']).",
                },
                "include_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional whitelist of columns to keep.",
                },
            },
            "required": ["input_dir", "output_excel"],
        },
        description="Merge all .jsonl extraction files in `input_dir` into a single Excel workbook.",
    )
    def write_excel(
        self,
        input_dir: str,
        output_excel: str,
        drop_columns: Optional[List[str]] = None,
        include_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return dataset_construction(
            input_dir=input_dir,
            output_excel=output_excel,
            drop_columns=drop_columns,
            include_columns=include_columns,
        )

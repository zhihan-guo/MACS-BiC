"""
Dataset construction tool.

Merges all per-DOI JSONL extraction files in an input folder into a single
Excel workbook. The shape of each JSONL record matches the writer used by
``agent/utils/utils.py::get_final_output``:

    {
        "doi": "...",
        "pdf": "...",
        "table_and_charts": "...",
        "text": "...",
        "qa": {"<question text>": "<answer>", ...},
        "model": "...",
        "success": true|false
    }

Each line becomes one row, with the ``qa`` mapping flattened into individual
columns so that every question gets its own column in the spreadsheet.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import pandas as pd


def _iter_jsonl_files(input_dir: str) -> List[str]:
    if not os.path.isdir(input_dir):
        return []
    out = []
    for name in sorted(os.listdir(input_dir)):
        if name.lower().endswith(".jsonl"):
            out.append(os.path.join(input_dir, name))
    return out


def _flatten_record(record: Dict[str, Any]) -> Dict[str, Any]:
    flat = {k: v for k, v in record.items() if k != "qa"}
    qa = record.get("qa") or {}
    if isinstance(qa, dict):
        for q, a in qa.items():
            flat[str(q)] = a
    else:
        flat["qa"] = qa
    return flat


def dataset_construction(
    input_dir: str,
    output_excel: str,
    *,
    include_columns: Optional[List[str]] = None,
    sheet_name: str = "extractions",
    drop_columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Merge per-paper JSONL files in ``input_dir`` into ``output_excel``.

    Parameters
    ----------
    input_dir : str
        Folder containing ``*.jsonl`` files (one per DOI).
    output_excel : str
        Destination ``.xlsx`` file path. Parent dir will be created if missing.
    include_columns : list[str], optional
        If provided, restrict the final spreadsheet to these columns (plus
        ``doi``).
    sheet_name : str
        Excel sheet name (default ``extractions``).
    drop_columns : list[str], optional
        Columns to exclude from the output (e.g. ``["text", "table_and_charts"]``).

    Returns
    -------
    dict
        ``{"success": bool, "data": {"output_excel": str, "row_count": int, "files": int}}``
    """
    files = _iter_jsonl_files(input_dir)
    if not files:
        return {
            "success": False,
            "error": f"No .jsonl files found in {input_dir!r}",
        }

    rows: List[Dict[str, Any]] = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    rows.append(_flatten_record(record))
        except OSError as exc:
            return {"success": False, "error": f"Failed to read {path}: {exc}"}

    if not rows:
        return {"success": False, "error": "No valid records parsed from JSONL files."}

    df = pd.DataFrame(rows)

    if drop_columns:
        df = df.drop(columns=[c for c in drop_columns if c in df.columns], errors="ignore")

    if include_columns:
        keep = [c for c in include_columns if c in df.columns]
        if "doi" in df.columns and "doi" not in keep:
            keep = ["doi"] + keep
        df = df[keep]

    os.makedirs(os.path.dirname(os.path.abspath(output_excel)) or ".", exist_ok=True)
    df.to_excel(output_excel, sheet_name=sheet_name, index=False)

    return {
        "success": True,
        "data": {
            "output_excel": output_excel,
            "row_count": int(len(df)),
            "files": len(files),
        },
    }

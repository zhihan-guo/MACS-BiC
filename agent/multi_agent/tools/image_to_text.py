"""
Image-to-text tool (Gemini-based figure/table translator).

Mirrors the ``chart_to_table_prompt`` flow that already exists in
``agent/utils/utils.py``: for each ``.jpg``/``.jpeg`` figure produced by MinerU
we ask Gemini-2.5-pro (served through an OpenAI-compatible proxy) to render the
chart/table as a markdown table.  The aggregated translation is cached on disk
as a JSONL file keyed by DOI, exactly as the existing extraction pipeline
expects.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from openai import OpenAI


CHART_TO_TABLE_PROMPT = '''Convert given chart or table to a markdown format table.
If given image is not a table or chart, use a short phrase to describe it.
For each chart: 1. Extract only the main value (ignore error sticks/text annotations like '% change')
2. Identify axis units: Convert units when mismatched (e.g., from m to mm: multiply by 1,000); Keep original values if units match requirements
3. Validate against context: Cross-check extracted values with textual results in the paper.
Your output format should be markdown text. Provide the answer as float numbers, rounded to two decimal places.
Your answers should show difference between values.
Then generate a one-sentence table captain.
'''


def _sanitize(name: str) -> str:
    for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, "_")
    return name


def _encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _collect_jpgs(folder: Path) -> List[Path]:
    return sorted(list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")))


def image_to_text(
    doi: str,
    images_dir: str,
    output_dir: str,
    *,
    api_key: Optional[str] = None,
    base_url: str = "https://az.gptplus5.com/v1",
    model: str = "gemini-2.5-pro",
    prompt: str = CHART_TO_TABLE_PROMPT,
) -> Dict[str, Any]:
    """
    Convert every figure/table image of a paper into markdown text.

    Caches the result to ``<output_dir>/<sanitized_doi>.jsonl`` so subsequent
    runs can short-circuit.

    Parameters
    ----------
    doi : str
        DOI of the paper (used to derive the cache filename).
    images_dir : str
        Folder produced by MinerU containing the paper's figure images.
    output_dir : str
        Folder where the cached JSONL translation will be written.
    api_key : str, optional
        API key for the Gemini-compatible endpoint. Falls back to
        ``os.environ['GEMINI_API_KEY']`` then ``os.environ['OPENAI_API_KEY']``.

    Returns
    -------
    dict
        ``{"success": bool, "data": {"doi": str, "jsonl": str, "table_and_charts": str, "image_count": int}}``
    """
    os.makedirs(output_dir, exist_ok=True)

    safe = _sanitize(doi)
    out_path = os.path.join(output_dir, f"{safe}.jsonl")

    if os.path.exists(out_path):
        df = pd.read_json(out_path, lines=True)
        return {
            "success": True,
            "data": {
                "doi": doi,
                "jsonl": out_path,
                "table_and_charts": df["table_and_charts"][0] if "table_and_charts" in df else "",
                "image_count": int(df["image_count"][0]) if "image_count" in df else 0,
                "status": "cached",
            },
        }

    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        return {
            "success": False,
            "error": "No API key provided (set GEMINI_API_KEY or OPENAI_API_KEY).",
        }

    jpgs = _collect_jpgs(Path(images_dir))
    if not jpgs:
        record = {"doi": doi, "table_and_charts": "", "image_count": 0}
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"success": True, "data": {**record, "jsonl": out_path, "status": "no_images"}}

    client = OpenAI(base_url=base_url, api_key=key)

    sections: List[str] = []
    for idx, img_path in enumerate(jpgs, start=1):
        try:
            b64 = _encode_image(img_path)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                            },
                        ],
                    }
                ],
            )
            text = (response.choices[0].message.content or "").strip()
            sections.append(f"### Image {idx}: {img_path.name}\n\n{text}\n")
        except Exception as exc:
            sections.append(f"### Image {idx}: {img_path.name}\n\n[ERROR] {exc}\n")

    table_and_charts = "\n\n---\n\n".join(sections).strip()
    record = {"doi": doi, "table_and_charts": table_and_charts, "image_count": len(jpgs)}
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "success": True,
        "data": {**record, "jsonl": out_path, "status": "generated"},
    }

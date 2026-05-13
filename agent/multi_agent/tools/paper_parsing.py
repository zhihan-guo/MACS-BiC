"""
Paper parsing tool (MinerU wrapper).

MinerU (https://github.com/opendatalab/mineru) converts PDFs into LLM-ready
markdown + figure images.  The CLI usage is::

    mineru -p <pdf_or_dir> -o <output_dir> [-b pipeline|vlm-transformers|vlm-vllm-engine]

For each input PDF MinerU writes::

    <output_dir>/<pdf_stem>/auto/<pdf_stem>.md         # markdown text
    <output_dir>/<pdf_stem>/auto/images/*.jpg          # extracted figures

This tool runs MinerU as a subprocess and returns the per-DOI markdown and
image-folder paths so downstream agents (paper_reader) can pick them up.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from typing import Any, Dict, Iterable, List, Optional


def _stem(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _run_mineru(
    pdf_path: str,
    output_dir: str,
    backend: str,
    extra_args: Optional[List[str]] = None,
    timeout: int = 60 * 30,
) -> Dict[str, Any]:
    """Run MinerU on a single PDF and return stdout/stderr metadata."""
    cmd: List[str] = ["mineru", "-p", pdf_path, "-o", output_dir, "-b", backend]
    if extra_args:
        cmd.extend(extra_args)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {
            "success": False,
            "error": (
                "mineru CLI not found in PATH. Install with "
                "`pip install --upgrade 'mineru[core]'` and verify with `mineru --version`."
            ),
            "command": " ".join(shlex.quote(c) for c in cmd),
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"mineru timed out after {timeout}s",
            "command": " ".join(shlex.quote(c) for c in cmd),
        }

    return {
        "success": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-2000:] if proc.stdout else "",
        "stderr": proc.stderr[-2000:] if proc.stderr else "",
        "command": " ".join(shlex.quote(c) for c in cmd),
    }


def paper_parsing(
    pdf_paths: Iterable[str],
    output_dir: str,
    *,
    backend: str = "pipeline",
    skip_existing: bool = True,
    extra_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Parse one or more PDFs into markdown + figure images using MinerU.

    Parameters
    ----------
    pdf_paths : iterable of str
        Paths to the input PDF files.
    output_dir : str
        Root output folder. MinerU will create ``<output_dir>/<pdf_stem>/auto``
        sub-folders.
    backend : str
        MinerU backend. One of ``pipeline`` (default, CPU-friendly),
        ``vlm-transformers`` or ``vlm-vllm-engine``.
    skip_existing : bool
        If True and ``<output_dir>/<pdf_stem>/auto/<pdf_stem>.md`` already exists
        the PDF is treated as already parsed and skipped.

    Returns
    -------
    dict
        ``{"success": bool, "data": {"parsed": [...], "failed": [...], "output_dir": str}}``
        Each ``parsed`` entry contains ``pdf``, ``markdown``, ``images`` paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    parsed: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []

    for pdf_path in pdf_paths:
        if not pdf_path or not os.path.exists(pdf_path):
            failed.append({"pdf": pdf_path, "reason": "file not found"})
            continue

        stem = _stem(pdf_path)
        md_path = os.path.join(output_dir, stem, "auto", f"{stem}.md")
        images_dir = os.path.join(output_dir, stem, "auto", "images")

        if skip_existing and os.path.exists(md_path):
            parsed.append({
                "pdf": pdf_path,
                "markdown": md_path,
                "images": images_dir,
                "status": "cached",
            })
            continue

        result = _run_mineru(pdf_path, output_dir, backend, extra_args)
        if result.get("success") and os.path.exists(md_path):
            parsed.append({
                "pdf": pdf_path,
                "markdown": md_path,
                "images": images_dir,
                "status": "parsed",
            })
        else:
            failed.append({
                "pdf": pdf_path,
                "reason": result.get("error") or result.get("stderr") or "mineru failed",
                "command": result.get("command"),
            })

    return {
        "success": True,
        "data": {"parsed": parsed, "failed": failed, "output_dir": output_dir},
    }

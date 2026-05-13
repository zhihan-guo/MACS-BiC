"""
Paper download tool.

Downloads full-text PDFs for a list of DOIs using the Web of Science (WoS) and
publisher-resolved links. The implementation:

1. Sanitises the DOI to a safe file name (e.g. ``10.1016/j.foo.2024`` ->
   ``10.1016_j.foo.2024.pdf``).
2. Looks up the full-text URL via the WoS Starter API (when an API key is
   available), otherwise resolves the DOI through ``https://doi.org`` and
   follows redirects to the publisher landing page.
3. Tries to fetch the PDF directly from the resolved URL.
4. Saves the PDF to ``output_dir/<sanitised>.pdf``.

The function returns a structured summary listing successes and failures so the
calling agent can react accordingly (e.g. retry, escalate).
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterable, List, Optional

import requests


WOS_ENDPOINT = "https://api.clarivate.com/apis/wos-starter/v1/documents"
USER_AGENT = "MACS-BiC-Downloader/1.0 (+https://github.com/macs-bic)"


def _sanitize_doi(doi: str) -> str:
    safe = doi.strip()
    for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
        safe = safe.replace(ch, '_')
    return safe


def _resolve_pdf_url_via_wos(doi: str, api_key: str, timeout: int = 30) -> Optional[str]:
    headers = {"X-ApiKey": api_key, "Accept": "application/json"}
    params = {"db": "WOS", "q": f'DO=("{doi}")', "limit": 1}
    try:
        r = requests.get(WOS_ENDPOINT, headers=headers, params=params, timeout=timeout)
    except requests.RequestException:
        return None
    if r.status_code != 200 or not r.content:
        return None
    payload = r.json() or {}
    records = payload.get("hits") or []
    for rec in records:
        links = rec.get("links") or {}
        url = links.get("openAccessUrl") or links.get("fullTextUrl") or links.get("pdf")
        if url:
            return url
    return None


def _resolve_pdf_url_via_doi(doi: str, timeout: int = 30) -> Optional[str]:
    try:
        r = requests.get(
            f"https://doi.org/{doi}",
            headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,text/html"},
            allow_redirects=True,
            timeout=timeout,
        )
    except requests.RequestException:
        return None
    content_type = (r.headers.get("Content-Type") or "").lower()
    if "pdf" in content_type:
        return r.url
    return None


def _download_pdf(url: str, dest_path: str, timeout: int = 60) -> bool:
    try:
        with requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/pdf"},
            stream=True,
            timeout=timeout,
        ) as r:
            if r.status_code != 200:
                return False
            content_type = (r.headers.get("Content-Type") or "").lower()
            if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                return False
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
            return True
    except requests.RequestException:
        return False


def paper_download(
    dois: Iterable[str],
    output_dir: str,
    *,
    api_key: Optional[str] = None,
    sleep_between: float = 0.2,
) -> Dict[str, Any]:
    """
    Download PDFs for a list of DOIs into ``output_dir``.

    Parameters
    ----------
    dois : iterable of str
        DOIs to download.
    output_dir : str
        Directory where the PDFs will be written (created if missing).
    api_key : str, optional
        WoS API key for resolving full-text URLs.  Falls back to
        ``os.environ['WOS_API_KEY']``.

    Returns
    -------
    dict
        ``{"success": bool, "data": {"downloaded": [...], "failed": [...], "output_dir": str}}``
    """
    os.makedirs(output_dir, exist_ok=True)
    key = api_key or os.environ.get("WOS_API_KEY")

    downloaded: List[Dict[str, str]] = []
    failed: List[Dict[str, str]] = []

    for doi in dois:
        doi = (doi or "").strip()
        if not doi:
            continue

        safe = _sanitize_doi(doi)
        dest = os.path.join(output_dir, f"{safe}.pdf")
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            downloaded.append({"doi": doi, "path": dest, "status": "cached"})
            continue

        url: Optional[str] = None
        if key:
            url = _resolve_pdf_url_via_wos(doi, key)
        if not url:
            url = _resolve_pdf_url_via_doi(doi)

        if not url:
            failed.append({"doi": doi, "reason": "no resolvable PDF URL"})
            time.sleep(sleep_between)
            continue

        ok = _download_pdf(url, dest)
        if ok:
            downloaded.append({"doi": doi, "path": dest, "status": "downloaded", "url": url})
        else:
            failed.append({"doi": doi, "reason": f"download failed from {url}"})
        time.sleep(sleep_between)

    return {
        "success": True,
        "data": {
            "downloaded": downloaded,
            "failed": failed,
            "output_dir": output_dir,
        },
    }

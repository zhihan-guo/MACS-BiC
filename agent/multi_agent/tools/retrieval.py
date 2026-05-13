"""
Retrieval tool.

Given a research `domain` (a free-text query, e.g. "biochar concrete carbon
footprint") this tool searches the Web of Science (WoS) Starter / Expanded API
and returns the list of DOIs of all matching papers.

Requirements
------------
- A WoS API key. The function reads it from the ``WOS_API_KEY`` environment
  variable, or accepts it explicitly via the ``api_key`` argument.
- Network access to ``https://api.clarivate.com/apis/wos-starter/v1``.

The function paginates through every page of the result set and returns a
de-duplicated list of DOIs.  It is intentionally written to be tolerant of
missing keys / partial responses since the WoS payload schema varies between
records.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests


WOS_ENDPOINT = "https://api.clarivate.com/apis/wos-starter/v1/documents"
DEFAULT_PAGE_SIZE = 50
DEFAULT_DB = "WOS"


def _build_query(domain: str, keywords: Optional[List[str]] = None) -> str:
    """Build a WoS topic query (TS=...) from a domain string and optional keywords."""
    domain = (domain or "").strip()
    parts: List[str] = []
    if domain:
        parts.append(f'"{domain}"')
    if keywords:
        parts.extend([f'"{kw.strip()}"' for kw in keywords if kw.strip()])
    if not parts:
        raise ValueError("retrieval_search: at least one of `domain` or `keywords` must be provided.")
    return "TS=(" + " AND ".join(parts) + ")"


def retrieval_search(
    domain: str,
    keywords: Optional[List[str]] = None,
    *,
    api_key: Optional[str] = None,
    max_records: int = 1000,
    page_size: int = DEFAULT_PAGE_SIZE,
    db: str = DEFAULT_DB,
    request_timeout: int = 30,
) -> Dict[str, Any]:
    """
    Search WoS for papers in the requested domain and return their DOIs.

    Parameters
    ----------
    domain : str
        High-level research domain, e.g. "biochar-integrated construction materials".
    keywords : list[str], optional
        Extra keywords that are AND-ed with the domain.
    api_key : str, optional
        WoS API key. Falls back to ``os.environ['WOS_API_KEY']``.
    max_records : int
        Upper bound on number of records to retrieve (defaults to 1000).
    page_size : int
        Number of records per WoS page (max 50 for the Starter API).
    db : str
        Database to search (defaults to ``WOS``).

    Returns
    -------
    dict
        ``{"success": bool, "data": {"query": str, "count": int, "dois": [...]}}``
    """
    key = api_key or os.environ.get("WOS_API_KEY")
    if not key:
        return {
            "success": False,
            "error": "WOS_API_KEY is not set. Provide `api_key` or export WOS_API_KEY.",
        }

    query = _build_query(domain, keywords)
    headers = {"X-ApiKey": key, "Accept": "application/json"}

    dois: List[str] = []
    seen: set[str] = set()
    page = 1
    total_fetched = 0

    while total_fetched < max_records:
        params = {
            "db": db,
            "q": query,
            "limit": min(page_size, max_records - total_fetched),
            "page": page,
        }
        try:
            resp = requests.get(WOS_ENDPOINT, headers=headers, params=params, timeout=request_timeout)
        except requests.RequestException as exc:
            return {"success": False, "error": f"WoS request failed: {exc}", "data": {"dois": dois}}

        if resp.status_code == 429:
            time.sleep(2)
            continue
        if resp.status_code >= 400:
            return {
                "success": False,
                "error": f"WoS HTTP {resp.status_code}: {resp.text[:300]}",
                "data": {"dois": dois},
            }

        payload = resp.json() if resp.content else {}
        records = payload.get("hits") or payload.get("Data", {}).get("Records", {}).get("records", {}).get("REC", [])
        if not records:
            break

        for rec in records:
            doi = _extract_doi(rec)
            if doi and doi not in seen:
                seen.add(doi)
                dois.append(doi)

        total_fetched += len(records)
        if len(records) < params["limit"]:
            break
        page += 1

    return {
        "success": True,
        "data": {"query": query, "count": len(dois), "dois": dois},
    }


def _extract_doi(record: Dict[str, Any]) -> Optional[str]:
    """Best-effort DOI extraction across WoS Starter / Expanded payload shapes."""
    if not isinstance(record, dict):
        return None

    if isinstance(record.get("identifiers"), dict):
        doi = record["identifiers"].get("doi")
        if doi:
            return str(doi).strip()

    static_data = record.get("static_data") or {}
    summary = static_data.get("summary") or {}
    identifiers = summary.get("identifiers") or {}
    if "doi" in identifiers:
        return str(identifiers["doi"]).strip()

    for k in ("DOI", "doi"):
        if k in record and record[k]:
            return str(record[k]).strip()

    return None

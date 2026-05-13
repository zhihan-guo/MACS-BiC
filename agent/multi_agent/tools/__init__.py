"""
Tools package for the MACS-BiC multi-agent system.

Six tools are exposed:
    1. retrieval               - search Web of Science (WoS) for DOIs by domain
    2. paper_download          - download PDFs from WoS by DOI
    3. paper_parsing           - run MinerU to convert PDFs to markdown + figures
    4. image_to_text           - convert figures/tables to markdown text via Gemini
    5. carbon_footprint        - compute LCA carbon footprint of a mixture
    6. dataset_construction    - merge per-paper JSONL extractions into a final Excel
"""

from .retrieval import retrieval_search
from .paper_download import paper_download
from .paper_parsing import paper_parsing
from .image_to_text import image_to_text
from .carbon_footprint import carbon_footprint_calculating
from .dataset_construction import dataset_construction

__all__ = [
    "retrieval_search",
    "paper_download",
    "paper_parsing",
    "image_to_text",
    "carbon_footprint_calculating",
    "dataset_construction",
]

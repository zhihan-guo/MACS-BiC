"""
Agents package for the MACS-BiC multi-agent system.

Five collaborating agents:

    PlannerAgent       - turns a user-supplied domain into a research plan.
    CoordinatorAgent   - executes the plan by delegating to specialised agents.
    PaperReaderAgent   - extracts structured Q&A from a paper PDF + figure text.
    DataWriterAgent    - merges per-paper JSONL outputs into a final Excel.
    JudgerAgent        - validates accuracy / formatting and triggers re-runs.
"""

from .planner import PlannerAgent
from .coordinator import CoordinatorAgent
from .paper_reader import PaperReaderAgent
from .data_writer import DataWriterAgent
from .judger import JudgerAgent

__all__ = [
    "PlannerAgent",
    "CoordinatorAgent",
    "PaperReaderAgent",
    "DataWriterAgent",
    "JudgerAgent",
]

"""RFP Autopilot: draft security questionnaire answers from an approved answer library."""
from .drafter import ExtractiveDrafter, LLMDrafter
from .library import ApprovedAnswer, load_library
from .pipeline import Thresholds, process_workbook
from .retriever import Retriever

__all__ = [
    "ApprovedAnswer", "ExtractiveDrafter", "LLMDrafter", "Retriever",
    "Thresholds", "load_library", "process_workbook",
]
__version__ = "0.1.0"

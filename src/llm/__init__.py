"""LLM integration for extracting job/training opportunities."""

from .extractor import extract_training_info_from_chat as extract_opportunities

__all__ = ['extract_opportunities']

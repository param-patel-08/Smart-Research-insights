"""
Smarter Research Insights (SRI) package
Tools for ingesting papers from OpenAlex API
"""
from .ingest_openalex import run_initial_ingestion, run_incremental_ingestion, run_test_ingestion

__all__ = [
    'run_initial_ingestion',
    'run_incremental_ingestion',
    'run_test_ingestion',
]

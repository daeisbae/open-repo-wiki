"""Processing stages for the ECS Fargate processor.

Each stage handles a specific part of the repository processing pipeline:
- fetch_details: Fetch repository metadata from GitHub
- fetch_tree: Fetch complete file tree from GitHub
- filter_tree: Apply whitelist/blacklist filters
- summarize: Generate AI summaries for files and folders
- finalize: Update job status to SUCCEEDED
"""

from services.processor.stages.fetch_details import FetchDetailsStage
from services.processor.stages.fetch_tree import FetchTreeStage
from services.processor.stages.filter_tree import FilterTreeStage
from services.processor.stages.summarize import SummarizeStage
from services.processor.stages.finalize import FinalizeStage

__all__ = [
    "FetchDetailsStage",
    "FetchTreeStage",
    "FilterTreeStage",
    "SummarizeStage",
    "FinalizeStage",
]

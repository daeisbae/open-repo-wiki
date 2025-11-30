"""
Custom Prometheus metrics for OpenRepoWiki.

These metrics are persisted in Prometheus and won't be lost on app restart.
They can be visualized in Grafana dashboards.
"""
from prometheus_client import Counter, Histogram, Gauge

# ============================================================================
# Repository Processing Metrics
# ============================================================================

# Counter: Total number of repository summarizations
REPO_SUMMARIZATIONS_TOTAL = Counter(
    'openrepowiki_repo_summarizations_total',
    'Total number of repository summarization requests',
    ['owner', 'repo', 'status']  # status: success, failed
)

# Histogram: Time taken to process entire repository
REPO_PROCESSING_DURATION = Histogram(
    'openrepowiki_repo_processing_duration_seconds',
    'Time spent processing entire repository',
    ['owner', 'repo'],
    buckets=[10, 30, 60, 120, 300, 600, 1200, 1800, 3600]  # Up to 1 hour
)

# ============================================================================
# Step-by-Step Processing Metrics
# ============================================================================

# Histogram: Duration of each processing step
STEP_DURATION = Histogram(
    'openrepowiki_step_duration_seconds',
    'Time spent on each processing step',
    ['step'],  # step: fetch_details, fetch_tree, filter_tree, insert_folders, summarize_files, summarize_folders
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600]
)

# Counter: Step completion count
STEP_COMPLETED = Counter(
    'openrepowiki_step_completed_total',
    'Number of times each step completed',
    ['step', 'status']  # status: success, failed
)

# ============================================================================
# File Processing Metrics
# ============================================================================

# Counter: Total files processed
FILES_PROCESSED_TOTAL = Counter(
    'openrepowiki_files_processed_total',
    'Total number of files processed',
    ['status']  # status: success, failed, skipped
)

# Histogram: Time to summarize a single file
FILE_SUMMARIZATION_DURATION = Histogram(
    'openrepowiki_file_summarization_duration_seconds',
    'Time spent summarizing a single file',
    buckets=[0.5, 1, 2, 5, 10, 20, 30, 60]
)

# ============================================================================
# Folder Processing Metrics
# ============================================================================

# Counter: Total folders processed
FOLDERS_PROCESSED_TOTAL = Counter(
    'openrepowiki_folders_processed_total',
    'Total number of folders processed',
    ['status']  # status: success, failed
)

# Histogram: Time to summarize a single folder
FOLDER_SUMMARIZATION_DURATION = Histogram(
    'openrepowiki_folder_summarization_duration_seconds',
    'Time spent summarizing a single folder',
    buckets=[0.5, 1, 2, 5, 10, 20, 30, 60]
)

# ============================================================================
# LLM API Metrics
# ============================================================================

# Counter: LLM API calls
LLM_API_CALLS_TOTAL = Counter(
    'openrepowiki_llm_api_calls_total',
    'Total number of LLM API calls',
    ['provider', 'model', 'status']  # status: success, failed, retry
)

# Histogram: LLM API response time
LLM_API_DURATION = Histogram(
    'openrepowiki_llm_api_duration_seconds',
    'Time spent waiting for LLM API response',
    ['provider', 'model'],
    buckets=[0.5, 1, 2, 5, 10, 20, 30, 60, 120]
)

# Counter: LLM tokens used
LLM_TOKENS_USED = Counter(
    'openrepowiki_llm_tokens_total',
    'Total tokens used in LLM API calls',
    ['provider', 'model', 'type']  # type: input, output
)

# ============================================================================
# GitHub API Metrics
# ============================================================================

# Counter: GitHub API calls
GITHUB_API_CALLS_TOTAL = Counter(
    'openrepowiki_github_api_calls_total',
    'Total number of GitHub API calls',
    ['endpoint', 'status']  # endpoint: repo_details, repo_tree, file_content
)

# Histogram: GitHub API response time
GITHUB_API_DURATION = Histogram(
    'openrepowiki_github_api_duration_seconds',
    'Time spent waiting for GitHub API response',
    ['endpoint'],
    buckets=[0.1, 0.25, 0.5, 1, 2, 5, 10, 30]
)

# ============================================================================
# Search Metrics
# ============================================================================

# Counter: Search requests
SEARCH_REQUESTS_TOTAL = Counter(
    'openrepowiki_search_requests_total',
    'Total number of search requests',
    ['type']  # type: repository, file, folder
)

# Histogram: Search response time
SEARCH_DURATION = Histogram(
    'openrepowiki_search_duration_seconds',
    'Time spent processing search request',
    ['type'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]
)

# ============================================================================
# Active Processing Gauge
# ============================================================================

# Gauge: Currently processing repositories
REPOS_PROCESSING = Gauge(
    'openrepowiki_repos_processing',
    'Number of repositories currently being processed'
)

# Gauge: Queue size (if using Celery)
TASK_QUEUE_SIZE = Gauge(
    'openrepowiki_task_queue_size',
    'Number of tasks waiting in queue'
)

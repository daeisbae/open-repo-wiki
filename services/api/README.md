# API Lambda Handlers

This package contains the Lambda handlers for the OpenRepoWiki API.

## Lambda Entry Points

| Function | Handler | Description |
|----------|---------|-------------|
| Jobs Handler | `services.api.lambda_handler.jobs_handler` | POST/GET /jobs endpoints |
| Repos Handler | `services.api.lambda_handler.repos_handler` | GET /repos endpoints |

## API Endpoints

### Jobs API
- `POST /jobs` - Create a new processing job
- `GET /jobs/{jobId}` - Get job status

### Repos API
- `GET /repos/{repoId}/tree?branch=...&path=...` - List folder contents
- `GET /repos/{repoId}/page?branch=...&path=...` - Get page content

## Building Deployment Package

```bash
# Build the Lambda deployment package
./build_package.sh

# Output: dist/api-lambda-package.zip
```

## Package Structure

The deployment package includes:
```
api-lambda-package.zip
├── services/
│   ├── __init__.py
│   └── api/
│       ├── __init__.py
│       ├── lambda_handler.py    # Entry points
│       └── handlers/
│           ├── __init__.py
│           ├── jobs.py          # Jobs API handlers
│           └── repos.py         # Repos API handlers
├── shared/
│   ├── __init__.py
│   ├── models/                  # Data models
│   ├── storage/                 # DynamoDB/S3 clients
│   └── github/                  # GitHub client
└── [dependencies]               # boto3, aiohttp, etc.
```

## Environment Variables

The Lambda functions expect the following environment variables:

| Variable | Description |
|----------|-------------|
| `DDB_MAIN_TABLE` | DynamoDB main table name |
| `DDB_JOBS_TABLE` | DynamoDB jobs table name |
| `S3_BUCKET` | S3 artifacts bucket name |
| `STATE_MACHINE_ARN` | Step Functions state machine ARN |
| `MAX_CONCURRENT_JOBS` | Maximum concurrent jobs (default: 10) |
| `LOG_LEVEL` | Logging level (default: INFO) |

## Dependencies

See `requirements.txt` for Python dependencies:
- `boto3` - AWS SDK
- `aiohttp` - Async HTTP client
- `typing-extensions` - Type hints support

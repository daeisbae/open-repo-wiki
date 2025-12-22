# OpenRepoWiki Architecture

This document provides a comprehensive overview of the OpenRepoWiki serverless architecture on AWS.

## Overview

OpenRepoWiki is a fully serverless application that automatically generates wiki documentation for GitHub repositories using LLM-powered code analysis.

```mermaid
flowchart TB
    subgraph DNS["DNS Layer"]
        R53[("Route53")]
    end

    subgraph CDN["CDN Layer"]
        CF["CloudFront"]
    end

    subgraph Frontend["Frontend"]
        S3F[("S3 Static Assets")]
    end

    subgraph API["API Layer"]
        APIGW["API Gateway + Authorizer"]
        WAF["WAF Protection"]
        JobsLambda["Jobs Lambda"]
        ReposLambda["Repos Lambda"]
    end

    subgraph Processing["Processing Layer"]
        SFN["Step Functions"]
        ECS["ECS Fargate Processor"]
    end

    subgraph Data["Data Layer"]
        DDB[("DynamoDB")]
        S3A[("S3 Artifacts")]
        SM["Secrets Manager"]
    end

    subgraph External["External"]
        GH["GitHub API"]
        LLM["LLM Provider"]
    end

    R53 --> CF
    CF --> S3F
    CF --> APIGW
    WAF -.->|protects| APIGW
    APIGW --> JobsLambda
    APIGW --> ReposLambda
    JobsLambda --> SFN
    SFN --> ECS
    ECS --> DDB
    ECS --> S3A
    ECS --> SM
    ECS --> GH
    ECS --> LLM
    ReposLambda --> DDB
    ReposLambda --> S3A
```

---

## Components

### 1. Frontend Layer

| Component | Purpose |
|-----------|---------|
| **Route53** | DNS management. Routes `openrepowiki.xyz` → CloudFront, `api.*` → API Gateway |
| **ACM** | SSL/TLS certificates for custom domains (auto-renewed) |
| **CloudFront** | Global CDN with SSL termination. Caches static assets and routes API requests |
| **S3 Frontend** | Hosts the React + Vite static build with public-read access |

### 2. API Layer

| Component | Purpose |
|-----------|---------|
| **API Gateway** | REST API with resource-based routing (`/jobs`, `/repos`) |
| **Lambda Authorizer** | Validates HMAC-signed requests for protected endpoints (POST) |
| **Jobs Handler** | Creates analysis jobs and returns status (`POST /jobs`, `GET /jobs/{id}`) |
| **Repos Handler** | Returns repository tree and page content (`GET /repos/{id}/tree`, `/page`) |

### 3. Processing Layer

| Component | Purpose |
|-----------|---------|
| **Step Functions** | Orchestrates the multi-stage processing workflow with retries and error handling |
| **ECS Fargate** | Runs the containerized processor that fetches code and generates summaries |
| **LLM Provider** | External API (DeepSeek, Gemini, etc.) for AI-powered code summarization |

### 4. Data Layer

| Component | Purpose |
|-----------|---------|
| **DynamoDB Main** | Stores repositories, branches, and tree nodes (files/folders with summaries) |
| **DynamoDB Jobs** | Tracks job status and progress for real-time updates |
| **S3 Artifacts** | Stores large summaries (>4KB) that exceed DynamoDB item limits |

---

## Request Flow

### Creating an Analysis Job

```mermaid
flowchart LR
    User --> CloudFront --> APIGW[API Gateway]
    APIGW --> Auth[Authorizer]
    Auth --> Jobs[Jobs Lambda]
    Jobs --> DDB[(DynamoDB)]
    Jobs --> SFN[Step Functions]
    SFN --> ECS[ECS Fargate]
```

1. **User submits repository URL** via frontend
2. **Frontend signs the request** with HMAC-SHA256 (timestamp + method + path)
3. **Lambda Authorizer validates** the signature and timestamp (±5 min)
4. **Jobs Handler creates job** in DynamoDB with `PENDING` status
5. **Step Functions starts** the processing workflow
6. **ECS Fargate runs** the processor container

### Processing Workflow

```mermaid
flowchart TB
    SFN[Step Functions] --> ECS[ECS Fargate]
    ECS --> FETCH
    ECS --> FILTER
    ECS --> SUMMARIZE
    FETCH --> GitHub[GitHub API]
    SUMMARIZE --> LLM[LLM Provider]
    SUMMARIZE --> DDB[(DynamoDB)]
    SUMMARIZE --> S3[(S3 Artifacts)]
```

The processor runs three stages:

1. **FETCH** - Retrieves repository tree from GitHub API
2. **FILTER** - Removes non-essential files (binaries, lock files, etc.)
3. **SUMMARIZE** - Generates AI summaries for each file and folder

### Viewing Repository Wiki

```mermaid
flowchart LR
    User --> CloudFront --> APIGW[API Gateway]
    APIGW --> Repos[Repos Lambda]
    Repos --> DDB[(DynamoDB)]
    Repos --> S3[(S3)]
    DDB --> Response
    S3 --> Response
```

1. **User requests tree** → Returns folder structure with summary refs
2. **User clicks item** → Fetches full summary from DynamoDB or S3

---

## Security Architecture

### Network Security

```mermaid
flowchart TB
    subgraph VPC
        subgraph Public["Public Subnet"]
            NAT[NAT Gateway]
        end
        subgraph Private["Private Subnet"]
            ECS[ECS Fargate Tasks]
            VPCE[VPC Endpoints]
        end
    end
    
    ECS <--> NAT
    NAT --> Internet
    ECS --> VPCE
    VPCE --> DDB[(DynamoDB)]
    VPCE --> S3[(S3)]
    VPCE --> ECR[(ECR)]
    VPCE --> SM[Secrets Manager]
```

| Layer | Implementation |
|-------|----------------|
| **VPC Isolation** | ECS tasks run in private subnets with no public IPs |
| **NAT Gateway** | Allows outbound traffic to GitHub API and LLM providers |
| **VPC Endpoints** | Private connectivity to AWS services (no internet routing) |

### API Security

| Layer | Protection |
|-------|------------|
| **WAF** | Blocks malicious requests with AWS Managed Rules |
| **Rate Limiting** | 100 requests/5min for job creation, 2000/5min for reads |
| **HMAC Signing** | All POST requests require cryptographic signature |
| **CORS** | Restricted to `openrepowiki.xyz` origin only |

### WAF Rules

```
Priority 1: AWSManagedRulesCommonRuleSet     → Block common attacks (XSS, SQLi)
Priority 2: AWSManagedRulesKnownBadInputsRuleSet → Block known malicious patterns
Priority 3: RateLimitJobCreation             → 100 req/5min for POST /jobs
Priority 4: RateLimitGeneral                 → 2000 req/5min for all requests
```

### Request Authentication

Protected endpoints (POST /jobs) use HMAC-SHA256 signing:

```mermaid
sequenceDiagram
    participant Frontend
    participant Authorizer
    
    Frontend->>Frontend: Build message: timestamp:method:path
    Frontend->>Frontend: Sign with HMAC-SHA256
    Frontend->>Authorizer: Request + X-Timestamp + X-Signature
    Authorizer->>Authorizer: Validate timestamp (±5 min)
    Authorizer->>Authorizer: Rebuild expected signature
    Authorizer->>Authorizer: Compare signatures
    Authorizer-->>Frontend: Allow / Deny
```

### Data Security

| Layer | Implementation |
|-------|----------------|
| **Encryption at Rest** | DynamoDB uses server-side encryption (SSE), S3 uses AES-256 |
| **Secrets Management** | API keys stored in AWS Secrets Manager, not environment variables |
| **S3 Block Public Access** | All public access blocked; access via signed URLs only |
| **Point-in-Time Recovery** | DynamoDB PITR enabled for data protection |

### IAM Permissions

Each component has least-privilege access:

| Component | Permissions |
|-----------|-------------|
| **Jobs Lambda** | DynamoDB (read/write jobs), Step Functions (start execution) |
| **Repos Lambda** | DynamoDB (read main table), S3 (read artifacts) |
| **ECS Task** | DynamoDB (full access), S3 (read/write), Secrets Manager (read) |
| **Authorizer Lambda** | Secrets Manager (read signing key only) |

---

## Data Model

### DynamoDB Main Table

Stores repositories and tree nodes using a single-table design:

| Entity | PK | SK | Attributes |
|--------|----|----|------------|
| Repository | `REPO#{owner}/{name}` | `METADATA` | url, stars, default_branch |
| Branch | `REPO#{owner}/{name}` | `BRANCH#{branch}` | commit_sha, processed_at |
| Tree Node | `TREE#{repo_id}#{branch}` | `NODE#{path}` | type, name, summary_ref |

### DynamoDB Jobs Table

| Entity | PK | SK | Attributes |
|--------|----|----|------------|
| Job | `JOB#{job_id}` | `STATUS` | status, stage, progress, error |

---

## Processing Stages

### Stage 1: FETCH

```python
# Fetches repository tree from GitHub
tree = github.get_tree(owner, repo, branch, recursive=True)
# Returns: [{path, type, sha, size}, ...]
```

### Stage 2: FILTER

```python
# Removes non-essential files
excluded = ["node_modules/", "*.lock", "*.min.js", "*.png", ...]
filtered = [item for item in tree if not matches_exclude(item.path)]
```

### Stage 3: SUMMARIZE

```python
# Process files first (parallel with semaphore)
for file in files:
    content = github.fetch_file(file.path)
    summary = llm.summarize_code(content)  # Returns JSON: {usage, summary}
    store(file, summary)

# Process folders depth-first (uses child summaries)
for folder in sorted_by_depth_desc(folders):
    child_summaries = get_children(folder.path)
    summary = llm.summarize_folder(child_summaries)  # Includes dependency_graph
    store(folder, summary)
```

---

## Cost Optimization

| Strategy | Savings |
|----------|---------|
| **Lambda** | Pay-per-invocation, $0 when idle |
| **DynamoDB On-Demand** | Pay-per-request, no capacity planning |
| **Fargate Spot** | Up to 70% discount on processing tasks |
| **CloudFront Caching** | Reduces origin requests for static assets |
| **VPC Endpoints** | Reduces NAT Gateway data transfer costs |

---

## Monitoring

| Service | Logs |
|---------|------|
| **Lambda** | `/aws/lambda/{function-name}` |
| **ECS** | `/ecs/{cluster}-processor` |
| **API Gateway** | Access logs + execution logs |
| **WAF** | Blocked requests, rate limit hits |

---

## Deployment

```bash
# 1. Deploy infrastructure
cd infra/terraform/env/prod
terraform apply

# 2. Build and push processor image
cd services/processor
docker build -t openrepowiki-processor .
aws ecr get-login-password | docker login --username AWS --password-stdin {ecr-url}
docker push {ecr-url}:latest

# 3. Deploy Lambda code
cd services/api
./build_package.sh
aws lambda update-function-code --function-name {name} --zip-file fileb://dist/package.zip

# 4. Deploy frontend
cd frontend
npm run build:prod
aws s3 sync dist/ s3://{bucket}/ --delete
aws cloudfront create-invalidation --distribution-id {id} --paths "/*"
```

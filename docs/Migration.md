# Migration: OpenRepoWiki → AWS (Static UI + API + Step Functions + ECS + DynamoDB + S3)

This document is a concrete checklist to migrate this repo from:
- Django web app + Celery background tasks
- Relational DB models (`Repository`, `Branch`, `Folder`, `File`, `Topic`)

…to an AWS architecture where:
- UI is static (S3 + CloudFront)
- Control plane is API Gateway + Lambda
- Data plane is a short-lived ECS Fargate task (per repo processing job)
- Workflow is Step Functions (to orchestrate and handle retries/timeouts)
- Metadata and job progress are stored in DynamoDB
- Large generated content is stored in S3 (DynamoDB stores pointers)

---

## 0) Target Architecture (What you’re building)

### 0.1 High-level flow
1. User submits `owner/repo` in the UI.
2. API `POST /jobs` creates a Job record in DynamoDB.
3. Step Functions execution starts and runs an ECS Fargate task.
4. ECS task:
   - fetches repo metadata/tree from GitHub
   - filters files (same logic you have today)
  - summarizes folders (and optionally files, depending on repo size limits)
   - writes results to DynamoDB (index + pointers) and S3 (large markdown/pages)
   - updates job progress in DynamoDB during each stage
5. UI polls API `GET /jobs/{jobId}` to show progress.
6. UI loads repo tree/pages via API `GET /repos/{repoId}/tree?...` and `GET /repos/{repoId}/page?...`.

### 0.2 Why Step Functions if you already use ECS
- Step Functions gives you retries/backoff, timeouts, and a per-job execution trace.
- ECS does the heavy work; Step Functions coordinates it.

---

## 1) IaC: Terraform (do this first)

You decided to use Terraform.

### 1.1 Terraform basics to set up
- Use local state (`terraform.tfstate`) for now.
- Add `terraform.tfstate*` and `.terraform/` to `.gitignore`.
- Keep separate state per environment by using separate folders (recommended) such as `env/dev` and `env/prod`.

Note: local state is fine for a single developer. If/when you collaborate or need safer recovery, migrate the backend to S3 + DynamoDB locking later.

Recommended Terraform layout:
- `infra/terraform/`
  - `env/dev/` and `env/prod/` (thin wrappers)
  - `modules/` (reusable modules: `dynamodb`, `s3`, `ecr`, `ecs`, `sfn`, `apigw`, `lambda`, `cloudfront`)

### 1.2 Naming and tagging
Decide your `project` name (e.g. `openrepowiki`) and tag all resources with:
- `Project`, `Environment`, `Owner`

---

## 2) Create the new repo structure (additive, keep current running)
Add these folders (don’t delete Django yet):
- `infra/terraform/` (Terraform code)
- `services/api/` (Lambda API handlers)
- `services/processor/` (ECS task source + Dockerfile)
- `frontend/` (static UI; can start minimal)
- `shared/` (GitHub client, data models, shared helpers)

Goal: you can deploy AWS pieces without breaking the current local app.

---

## 3) Data model migration: Django models → DynamoDB + S3

### 3.1 DynamoDB tables (start with 2 tables)
Create:

#### Table A: `OpenRepoWikiMain`
Purpose: repo metadata + tree index + summaries
- Partition key: `PK` (string)
- Sort key: `SK` (string)

Recommended item patterns:
- Repo:
  - `PK = REPO#<repoId>`
  - `SK = META`
  - attrs: owner, name, default_branch, stars, forks, language, github_url, created_at
- Branch:
  - `PK = REPO#<repoId>`
  - `SK = BRANCH#<branchName>`
  - attrs: last_commit_sha, commit_at, ai_summary_ref (S3 key)
- Tree nodes (folder/file index):
  - `PK = REPO#<repoId>#BRANCH#<branchName>`
  - `SK = NODE#<path>`
  - attrs:
    - type: `folder|file`
    - parent_path
    - name
    - sha
    - size
    - language
    - summary_ref (S3 key or inline short summary)

Optional GSIs (add only if you need them):
- `GSI1PK = REPO_LOOKUP#<owner>` + `GSI1SK = <repoName>` (lookup by owner/name)

#### Table B: `OpenRepoWikiJobs`
Purpose: job status + progress
- Partition key: `PK`
- Sort key: `SK`

Patterns:
- Job record:
  - `PK = JOB#<jobId>`
  - `SK = META`
  - attrs:
    - repo_owner, repo_name, branch
    - status: `PENDING|RUNNING|SUCCEEDED|FAILED`
    - stage: `FETCH_DETAILS|FETCH_TREE|FILTER|SUMMARIZE_FILES|SUMMARIZE_FOLDERS|FINALIZE`
    - processed, total
    - message
    - started_at, updated_at, finished_at
    - error (optional)

### 3.2 S3 bucket
Create a bucket, e.g. `openrepowiki-artifacts-<env>`.
Store:
- Generated markdown/wiki pages
- Folder summaries if large
- Repo-level summary if large

Suggested S3 key layout:
- `repos/<repoId>/branches/<branch>/pages/<path>.md`
- `repos/<repoId>/branches/<branch>/summaries/repo.md`

### 3.3 What NOT to store
- Do not store raw code blobs long-term unless you must.
- Fetch raw files from GitHub on-demand for viewing.

---

## 4) Replace Celery with Step Functions + ECS

### 4.1 Map current pipeline to new job stages
Current: `process_repository_task(owner, repo)` → calls `InsertRepoService.insertRepository()`.

New stages:
1. Create Job (Lambda)
2. Start ECS Processor (Step Functions)
3. Poll/Callback completion (Step Functions)
4. Finalize (Lambda)

### 4.2 Step Functions pattern (recommended)
Use **callback pattern** so SFN waits until ECS finishes.
- SFN passes a `TASK_TOKEN` to the ECS container as env var.
- ECS updates DynamoDB progress while running.
- ECS calls `SendTaskSuccess`/`SendTaskFailure` when done.

Why: You get clean success/failure + timeouts + retries at the workflow level.

### 4.3 ECS task responsibilities
In the container, port the logic from:
- `src/wiki_app/services.py` (`InsertRepoService`)
- `src/agent/*` (code splitter, prompt generator, dependency parser)
- `src/github/*` (repo fetch, filter)
- `src/llm/*` (provider abstraction)

Replace the Django ORM writes with:
- DynamoDB puts/updates
- S3 puts (for large output)

The ECS task should accept input via env vars:
- `REPO_OWNER`, `REPO_NAME`, `BRANCH`
- `JOB_ID`
- `DDB_MAIN_TABLE`, `DDB_JOBS_TABLE`, `S3_BUCKET`
- `GITHUB_TOKEN`
- LLM config (provider/model/key)
- Repo size / budget controls:
  - `MAX_FILES_FOR_FULL_SUMMARY` (integer)
    - If total filtered files exceeds this number, run **folder-only summarization** (skip file-level summarization records).
- `TASK_TOKEN` (only if using callback)

---

## 5) Build the new API (Lambda)

### 5.1 Endpoints (minimal)
Implement these first:
- `POST /jobs` → create job + start Step Functions execution
- `GET /jobs/{jobId}` → return status + stage + processed/total + message
- `GET /repos/{repoId}/tree?branch=...&path=...` → list folder contents (from DynamoDB)
- `GET /repos/{repoId}/page?branch=...&path=...` → return markdown/wiki content (DynamoDB pointer → S3 GET)

---

## 6) Build the static UI

### 6.0 UI parity requirement
Keep the static UI **as similar as the current UI as possible** (layout and behavior), including:
- Repo input + “processing/progress” view
- Left tree navigation for folders/files
- Content pane that renders the generated wiki/summaries

Use the existing Django templates as the visual/UX reference (don’t introduce new flows unless required by the migration).

### 6.1 MVP UI behavior
- Form to input `owner/repo`
- Job progress view (poll `GET /jobs/{jobId}`)
- Tree browser (calls `/tree` endpoint)
- Page view (calls `/page` endpoint)

Folder-only mode UX behavior (when repo is too large):
- Folder pages still render folder summaries.
- File pages should show expand. (Which will call the api to call additional file summarization) But we wouldn't send it unless it's requested. As requesting huge file summarization would cause lag

### 6.2 Hosting
- Deploy static assets to S3
- Put CloudFront in front
- API called via custom domain or API Gateway URL

---

## 7) Networking and cost controls (important)

### 7.1 Security-first VPC (recommended for this project)
If security is a top priority, run compute in a VPC using **private subnets**:
- ECS Fargate tasks run in private subnets with **no public IPs**.
- If Lambda needs VPC access (e.g., to call private resources), place those Lambdas in the VPC as well.

Important consequence: the processor must call **GitHub + LLM provider** (public internet). If ECS is in private subnets, you typically need **NAT Gateway** for outbound access.

To reduce NAT usage and tighten security:
- Add VPC endpoints where possible (traffic stays on AWS network):
  - Gateway endpoints: S3, DynamoDB
  - Interface endpoints: ECR (api + dkr), CloudWatch Logs, Secrets Manager, STS (and others you use)
- Keep NAT only for GitHub + LLM egress.

Terraform note: private subnets + NAT is the most common secure layout, but it increases cost. If cost becomes a problem, the fallback is running ECS in public subnets with public IPs plus strict security groups; that is simpler but weaker from an egress-control standpoint.

### 7.2 Concurrency guardrails
Because you want 1–2 typical and up to ~10:
- Set Step Functions + ECS desired concurrency limit (account/cluster)
- In the API, enforce `maxRunningJobs = 10` (DynamoDB query on jobs)

### 7.2.1 Large repo behavior (required)
Define an environment variable in the ECS processor:
- `MAX_FILES_FOR_FULL_SUMMARY`

Behavior:
- If total filtered file count `<= MAX_FILES_FOR_FULL_SUMMARY`: generate and store **file + folder** summarization records.
- If total filtered file count `> MAX_FILES_FOR_FULL_SUMMARY`: generate and store **folder-only** summaries and **do not** store per-file summarization records.

Implementation note:
- Still write the tree index (file/folder nodes) to DynamoDB so browsing works.
- For file nodes in folder-only mode, leave `summary_ref` empty (or set to a short sentinel value) so the API/UI knows file summaries are unavailable.

---

## 7.3 WAF (ingress protection)
Use AWS WAFv2 to protect your public entrypoints.

Recommended attachment points:
- **CloudFront Web ACL**: protects the static UI and (optionally) your API if you route API through CloudFront.
- **API Gateway (Regional) Web ACL**: protects API directly if clients call API Gateway without CloudFront.

Suggested baseline rules (start here):
- AWS Managed Rules: CommonRuleSet, KnownBadInputs, Amazon IP reputation
- Rate-based rule on `/jobs` and `/api/*` (mitigates brute force / accidental loops)
- Allow-list your own IPs for admin endpoints (optional)

Terraform resources you’ll use:
- `aws_wafv2_web_acl`
- `aws_wafv2_web_acl_association` (Regional)
- `aws_wafv2_web_acl` with CloudFront scope (for CloudFront)

Note: WAF protects **inbound** traffic. It does not control outbound traffic from ECS; that is handled via VPC design, endpoints, and (if you need it) egress firewalling.

---

## 7.4 Additional security defaults (recommended)
- **S3**: Block Public Access ON, use CloudFront Origin Access Control (OAC) so buckets are not directly reachable.
- **Encryption**:
  - DynamoDB encryption at rest (default) and consider KMS CMK if you need tighter key control.
  - S3 SSE-KMS for artifacts (recommended).
- **Secrets**: store GitHub token + LLM keys in AWS Secrets Manager; inject into ECS task at runtime.
- **IAM**: least-privilege task role for ECS (only DynamoDB tables + S3 prefix + logs + secrets + `states:SendTask*` if using callback).
---

## 8) Observability (minimum you should ship)
- ECS logs → CloudWatch Logs
- API logs → CloudWatch Logs
- Job progress → DynamoDB fields (stage, processed/total)
- Alarms:
  - SFN execution failed
  - ECS task failed
  - API 5xx spikes

---

## 9) Migration phases (do it in this order)

### Phase 1: Infrastructure skeleton
- Create DynamoDB tables
- Create S3 bucket
- Create ECR repositories (for the processor container image)
- Create ECS cluster + task definition
- Create Step Functions state machine
- Create API Gateway + Lambda for `POST /jobs` and `GET /jobs/{jobId}`

Terraform deliverable for Phase 1:
- `infra/terraform/` deploys: DynamoDB, S3, ECR, IAM roles/policies, ECS/Fargate task definition, Step Functions state machine, API Gateway, Lambda.

Acceptance criteria:
- `POST /jobs` starts a job
- Job status updates over time

### Phase 2: Processor port (core logic)
- Move GitHub crawling + filtering into ECS processor
- Write tree index to DynamoDB
- Write repo/folder summaries to S3 and pointers to DynamoDB

Acceptance criteria:
- Can browse tree and view generated pages

### Phase 3: UI cutover
- Build minimal static UI
- Deploy to S3+CloudFront

Acceptance criteria:
- End-to-end flow works without Django

### Phase 4: Remove Django/Celery/DB
- Delete or archive Django project files only after stable cutover

---

## 10) Implementation notes (based on current code)

### 10.1 Current progress reporting
Today, progress is stored in `Repository.process_status` in Django.

New approach:
- Store progress in `OpenRepoWikiJobs` (`stage`, `processed`, `total`, `message`).

### 10.2 GitHub tree and file fetch
You already use GitHub APIs:
- `fetch_github_repo_details`
- `fetch_github_repo_tree`
- `fetch_github_repo_file`

Keep that approach in ECS (it avoids clone complexity).

### 10.3 Keep your filtering rules
Port `github/filterfile.py` as-is so behavior stays consistent.

---

## 11) What you should do next (action list)
1. Create `infra/terraform/` using local state.
2. Deploy base infra (DynamoDB + S3 + ECR + IAM + ECS + Step Functions + API/Lambda).
3. Build the ECS processor image and push to ECR.
4. Implement the API endpoints for job create/status.
5. Port the summarization pipeline into the ECS container (replace Django ORM with DynamoDB/S3 writes).
6. Build and deploy the static UI.

---

## Appendix A: Suggested progress update contract
Update `OpenRepoWikiJobs` every 3–10 seconds or every N files:
- `stage`: string
- `processed`: number
- `total`: number
- `message`: short string

UI can render progress as:
- if `total > 0`: percentage = `processed/total`
- else: show stage + spinner

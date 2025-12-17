/**
 * API client for OpenRepoWiki backend.
 *
 * Implements:
 * - createJob: POST /jobs - Create new processing job
 * - getJob: GET /jobs/{jobId} - Get job status
 * - getTree: GET /repos/{repoId}/tree - List folder contents
 * - getPage: GET /repos/{repoId}/page - Get page content
 *
 * Requirements: 8.2, 8.3, 8.4
 */

import type { Job } from '../components/ProgressView';
import type { TreeNode } from '../components/TreeBrowser';
import type { PageContent } from '../components/PageViewer';

// API base URL - can be configured via environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * API error with code and message from backend.
 */
export class APIError extends Error {
  code: string;
  statusCode: number;

  constructor(code: string, message: string, statusCode: number) {
    super(message);
    this.name = 'APIError';
    this.code = code;
    this.statusCode = statusCode;
  }
}

/**
 * Parse API error response and throw APIError.
 */
async function handleErrorResponse(response: Response): Promise<never> {
  let errorData: { error?: { code?: string; message?: string } } = {};
  
  try {
    errorData = await response.json();
  } catch {
    // Response body is not JSON
  }

  const code = errorData.error?.code || 'UNKNOWN_ERROR';
  const message = errorData.error?.message || `Request failed with status ${response.status}`;
  
  throw new APIError(code, message, response.status);
}

/**
 * Result from creating a job, includes status to indicate if job is new, in progress, or completed.
 */
export interface CreateJobResult {
  jobId: string;
  status: 'new' | 'in_progress' | 'completed';
}

/**
 * Create a new processing job.
 *
 * POST /jobs
 *
 * @param owner - Repository owner
 * @param repo - Repository name
 * @param branch - Branch name (optional, defaults to 'main')
 * @returns Job ID and status
 * @throws APIError on failure
 *
 * Requirements: 8.2
 */
export async function createJob(
  owner: string,
  repo: string,
  branch?: string
): Promise<CreateJobResult> {
  const response = await fetch(`${API_BASE_URL}/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      owner,
      repo,
      branch: branch || 'main',
    }),
  });

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  const data = await response.json();
  
  // Determine status from backend message
  let status: 'new' | 'in_progress' | 'completed' = 'new';
  if (data.message === 'Job already in progress') {
    status = 'in_progress';
  } else if (data.message === 'Job already completed') {
    status = 'completed';
  }
  
  return { jobId: data.jobId, status };
}

/**
 * Get job status and progress.
 *
 * GET /jobs/{jobId}
 *
 * @param jobId - Job identifier
 * @returns Job object with status, stage, progress
 * @throws APIError on failure
 *
 * Requirements: 8.2
 */
export async function getJob(jobId: string): Promise<Job> {
  const response = await fetch(`${API_BASE_URL}/jobs/${encodeURIComponent(jobId)}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  return response.json();
}

/**
 * Get tree nodes (folder contents) for a repository.
 *
 * GET /repos/{repoId}/tree?branch=...&path=...
 *
 * @param repoId - Repository identifier (owner/name)
 * @param branch - Branch name
 * @param path - Parent path to query children for (empty string for root)
 * @returns Array of tree nodes
 * @throws APIError on failure
 *
 * Requirements: 8.3
 */
export async function getTree(
  repoId: string,
  branch: string,
  path: string
): Promise<TreeNode[]> {
  const params = new URLSearchParams({
    branch,
    path,
  });

  // Split repoId into owner/name for proper URL structure
  const [owner, name] = repoId.split('/');
  
  const response = await fetch(
    `${API_BASE_URL}/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/tree?${params}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  const data = await response.json();
  return data.nodes;
}

/**
 * Get page content (markdown summary) for a repository node.
 *
 * GET /repos/{repoId}/page?branch=...&path=...
 *
 * @param repoId - Repository identifier (owner/name)
 * @param branch - Branch name
 * @param path - Node path to get content for
 * @returns Page content with availability indicator
 * @throws APIError on failure
 *
 * Requirements: 8.4
 */
export async function getPage(
  repoId: string,
  branch: string,
  path: string
): Promise<PageContent> {
  const params = new URLSearchParams({
    branch,
    path,
  });

  // Split repoId into owner/name for proper URL structure
  const [owner, name] = repoId.split('/');
  
  const response = await fetch(
    `${API_BASE_URL}/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/page?${params}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  return response.json();
}

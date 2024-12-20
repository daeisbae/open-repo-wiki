import axios from "axios";

interface RepoResponse {
  owner: {
    login: string;
  };
  name: string;
  html_url: string;
  topics: string[];
  language: string;
  description: string;
  stargazers_count: number;
  forks_count: number;
  default_branch: string;
}

interface TreeResponse {
  sha: string;
  tree: TreeItem[];
}

interface TreeItem {
  path: string;
  type: 'file' | 'dir';
  sha: string;
  url: string;
}

interface RepoDetails {
  repoOwner: string;
  repoName: string;
  url: string;
  topics: string[];
  language: string;
  description: string;
  stars: number;
  forks: number;
  defaultBranch: string;
  sha: string;
}

interface RepoTreeResult {
  path: string;
  files: string[];
  subdirectories: RepoTreeResult[];
}

/**
 * Fetches details about a GitHub repository
 * @param {string} owner - The repository owner
 * @param {string} repo - The repository name
 * @returns {Promise<{language: string, description: string, stars: number, forks: number, url: string, topics: string[], repo_owner: string, repo_name: string, default_branch: string, sha: string}>}
 */
export async function fetchGithubRepoDetails(
  owner: string, 
  repo: string
): Promise<RepoDetails> {
  const repoUrl = `https://api.github.com/repos/${owner}/${repo}`;

  try {
    const repoResp = await axios.get<RepoResponse>(repoUrl);
    const repoData = repoResp.data;

    const treeUrl = `https://api.github.com/repos/${owner}/${repo}/git/trees/${repoData.default_branch}`;
    const treeResp = await axios.get<TreeResponse>(treeUrl);
    const treeData = treeResp.data;

    return {
      repoOwner: repoData.owner.login,
      repoName: repoData.name,
      url: repoData.html_url,
      topics: repoData.topics,
      language: repoData.language,
      description: repoData.description,
      stars: repoData.stargazers_count,
      forks: repoData.forks_count,
      defaultBranch: repoData.default_branch,
      sha: treeData.sha
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`GitHub API Error: ${error.response?.data?.message || error.message}`);
    }
    throw error;
  }
}

/**
 * Fetches Tree like structure of a GitHub repository folder
 * @param {string} owner - The repository owner
 * @param {string} repo - The repository name
 * @param {string} sha - The commit sha of the repository
 * @param {string} [path=''] - Optional path within repository
 * @returns {Promise<{path: string, files: Array<string>, subdirectories: Array}>}
 */
export async function fetchGithubRepoTree(
  owner: string,
  repo: string,
  sha: string,
  path: string = ''
): Promise<RepoTreeResult> {
  const contentsUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}?ref=${sha}`;

  try {
    const { data } = await axios.get<TreeItem[]>(contentsUrl);
    const result: RepoTreeResult = {
      path,
      files: [],
      subdirectories: []
    };

    for (const item of data) {
      if (item.type === 'file') {
        result.files.push(item.path);
      } else if (item.type === 'dir') {
        const subDir = await fetchGithubRepoTree(owner, repo, sha, item.path);
        result.subdirectories.push(subDir);
      }
    }

    return result;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Failed to fetch repo contents: ${error.response?.data?.message || error.message}`);
    }
    throw error;
  }
}

/**
 * Fetches a file from a GitHub repository
 * @param {string} owner - The repository owner
 * @param {string} repo - The repository name
 * @param {string} sha - The commit sha of the file to fetch
 * @param {string} path - The path of the file to fetch
 * @returns {Promise<String>}
 */
export async function fetchGithubRepoFile(
  owner: string,
  repo: string,
  sha: string,
  path: string
): Promise<string> {
  const codeUrl = `https://raw.githubusercontent.com/${owner}/${repo}/${sha}/${path}`;

  try {
    const response = await axios.get<string>(codeUrl);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Failed to fetch file: ${error.response?.data?.message || error.message}`);
    }
    throw error;
  }
}


import axios from 'axios'
import { GithubAuthConfig } from '@/github/config'

if(GithubAuthConfig.headers.Authorization) {
    axios.defaults.headers.common['Authorization'] = GithubAuthConfig.headers.Authorization
}

interface RepoResponse {
    owner: {
        login: string
    }
    name: string
    html_url: string
    topics: string[]
    language: string
    description: string
    stargazers_count: number
    forks_count: number
    default_branch: string
    pushed_at: Date
}

interface TreeResponse {
    sha: string
    tree: TreeItem[]
}

interface TreeItem {
    path: string
    type: 'file' | 'dir'
    sha: string
    url: string
}

interface RepoDetails {
    repoOwner: string
    repoName: string
    url: string
    topics: string[]
    language: string
    description: string
    stars: number
    forks: number
    defaultBranch: string
    sha: string
    commitAt: Date
}

export interface RepoTreeResult {
    path: string
    files: string[]
    subdirectories: RepoTreeResult[]
}

/**
 * Fetches details about a GitHub repository
 * @param {string} owner - The repository owner
 * @param {string} repo - The repository name
 * @returns {Promise<{language: string, description: string, stars: number, forks: number, url: string, topics: string[], repo_owner: string, repo_name: string, default_branch: string, sha: string}>}
 */
export async function fetchGithubRepoDetails(
    owner: string,
    repo: string,
): Promise<RepoDetails> {
    const repoUrl = `https://api.github.com/repos/${owner}/${repo}`

    try {
        const repoResp = await axios.get<RepoResponse>(
            repoUrl,
        )
        const repoData = repoResp.data

        const treeUrl = `https://api.github.com/repos/${owner}/${repo}/git/trees/${repoData.default_branch}`
        const treeResp = await axios.get<TreeResponse>(
            treeUrl,
        )
        const treeData = treeResp.data

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
            sha: treeData.sha,
            commitAt: repoData.pushed_at,
        }
    } catch (error) {
        if (axios.isAxiosError(error)) {
            throw new Error(
                `GitHub API Error: ${
                    error.response?.data?.message || error.message
                }`
            )
        }
        throw error
    }
}




interface GitTreeItem {
    path: string
    type: 'blob' | 'tree' // 'blob' = file, 'tree' = folder
    sha: string
}

/**
 * Fetches Tree like structure of a GitHub repository folder
 * @param {string} owner - The repository owner
 * @param {string} repo - The repository name
 * @param {string} commitSha - The commit sha of the repository
 * @returns {Promise<{path: string, files: Array<string>, subdirectories: Array}>}
 */
export async function fetchGithubRepoTree(
    owner: string,
    repo: string,
    commitSha: string
): Promise<RepoTreeResult> {
    const treeUrl = `https://api.github.com/repos/${owner}/${repo}/git/trees/${commitSha}?recursive=1`

    const { data } = await axios.get<{tree: GitTreeItem[]}>(treeUrl)

    const { tree } = data

    const rootResult: RepoTreeResult = {
        path: '',
        files: [],
        subdirectories: [],
    }

    const pathMap = new Map<string, RepoTreeResult>([
        ['', rootResult], // root
    ])

    for (const item of tree) {
        pathMap.set(item.path, {
            path: item.path,
            files: [],
            subdirectories: [],
        })
    }

    for (const item of tree) {
        const current = pathMap.get(item.path)!
        const parentPath = item.path.includes('/')
            ? item.path.slice(0, item.path.lastIndexOf('/'))
            : ''

        const parent = pathMap.get(parentPath)

        if (!parent) continue

        if (item.type === 'blob') {
            parent.files.push(item.path)
        } else if (item.type === 'tree') {
            parent.subdirectories.push(current)
        }
    }

    return rootResult
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
    path: string,
): Promise<string> {
    const codeUrl = `https://raw.githubusercontent.com/${owner}/${repo}/${sha}/${path}`

    try {
        const response = await axios.get<string>(
            codeUrl,
        )
        return response.data
    } catch (error) {
        if (axios.isAxiosError(error)) {
            throw new Error(
                `Failed to fetch file: ${
                    error.response?.data?.message || error.message
                }`
            )
        }
        throw error
    }
}

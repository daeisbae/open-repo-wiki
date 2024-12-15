import axios from "axios";

/**
 * Fetches details about a GitHub repository
 * @param {string} owner - The repository owner
 * @param {string} repo - The repository name
 * @returns {Promise<{language: string, description: string, stars: number, forks: number, url: string, topics: string[], repo_owner: string, repo_name: string, default_branch: string }>}
 */
export async function fetchGithubRepoDetails(owner, repo) {
    const repoUrl = `https://api.github.com/repos/${owner}/${repo}`;

    try {
        const { data } = await axios.get(repoUrl);
        return {
            repoOwner: data.owner.login,
            repoName: data.name,
            url: data.html_url,
            topics: data.topics,
            language: data.language,
            description: data.description,
            stars: data.stargazers_count,
            forks: data.forks_count,
            defaultBranch: data.default_branch,
        };
    } catch (error) {
        console.error("Error fetching repository details:", error);
        throw error;
    }
}

/**
 * Fetches contents of a GitHub repository
 * @param {string} owner - The repository owner
 * @param {string} repo - The repository name
 * @param {string} sha - The commit sha of the repository
 * @param {string} [path=''] - Optional path within repository
 * @returns {Promise<{path: string, files: Array<string>, subdirectories: Array}>}
 */
export async function fetchGithubRepoTree(owner, repo, sha, path = '') {
    const contentsUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}?ref=${sha}`;

    try {
        const { data } = await axios.get(contentsUrl);
        const result = {
            path: path,
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
        console.error("Error fetching repository contents:", error);
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
export async function fetchGithubRepoFile(owner, repo, sha, path) {
    const codeUrl = `https://raw.githubusercontent.com/${owner}/${repo}/${sha}/${path}`;

    try {
        return await axios.get(codeUrl);
    } catch (error) {
        console.error("Error fetching repository file:", error);
        throw error;
    }
}
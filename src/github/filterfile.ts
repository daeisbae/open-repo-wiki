import { RepoTreeResult } from '@/github/fetchrepo'

/**
 * Allow the files based on the regex patterns
 * @param {Array<string>} files - The files to allow (Provided by fetchGithubRepoTree)
 * @param {Array<string>} regexFilter - The regex patterns to allow the files
 * @returns {Array<string>} - The allowed files (files that match the patterns)
 */
export function whitelistedFile(
    files: string[],
    regexFilter: string[]
): string[] {
    const filterPatterns = regexFilter.map((pattern) => new RegExp(pattern))
    return files.filter((file) =>
        filterPatterns.some((pattern) => pattern.test(file.toLowerCase()))
    )
}

/**
 * Filter the files based on the regex patterns
 * @param {Array<string>} files - The files to filter (Provided by fetchGithubRepoTree)
 * @param {Array<string>} regexFilter - The regex patterns to allow the files
 * @returns {Array<string>} - The allowed files (folders that match the patterns)
 */
export function blacklistedFiles(files: string[], regexFilter: string[]) {
    const filterPatterns = regexFilter.map((pattern) => new RegExp(pattern))
    return files.filter((file) =>
    !filterPatterns.some((pattern) => pattern.test(file.toLowerCase()))
    )
}


/**
 * Filter the folders based on the regex patterns
 * @param {Array<RepoTreeResult>} folders - The folders to filter (Provided by fetchGithubRepoTree)
 * @param {Array<string>} regexFilter - The regex patterns to allow the folders
 * @returns {Array<RepoTreeResult>} - The allowed folders (folders that match the patterns)
 */
export function blacklistedFolder(
    folders: RepoTreeResult[],
    regexFilter: string[]
): RepoTreeResult[] {
    const filterPatterns = regexFilter.map((pattern) => new RegExp(pattern))
    return folders.filter(
        (folder) => !filterPatterns.some((pattern) => pattern.test(folder.path.toLowerCase()))
    )
}

export const whitelistedFilter = [
    '\\.py$',
    '\\.js$',
    '\\.ts$',
    '\\.java$',
    '\\.scala',
    '\\.md',
    '\\.cpp$',
    '\\.cc$',
    '\\.cxx$',
    '\\.hpp$',
    '\\.hxx$',
    '\\.h$',
    '\\.go$',
    '\\.rb$',
    '\\.rs$',
    '\\.php$',
]

export const blacklistedFile = [
    '__init__.py',
    'setup.py',
    'next-env.d.ts',
    'license.md',
    'contributor.md',
    'contributing.md',
    'contrib.md',
    'code_of_conduct.md',
    'security.md',
    'development.md',
    'funding.md',
    'pull_request_template.md',
    'issue_template.md'
]

export const blacklistedFilter = [
    'node_modules',
    '.github',
    '.vscode',
    '.idea',
    '.next',
    '.circleci',
    '.ci',
    '.dependabot',
    '.husky',
    'cmake',
    'contrib',
    '.devcontainer',
    'docker',
    'docs_src',
    'scripts',
    'third_party',
    'doc',
    'diagram',
    'changelog',
    'release',
    'requirements',
    'workflows',
    'test',
    'example',
    'img',
    'image',
    'assets',
    'build',
    'output',
    'temp',
    'tmp',
    'cache',
    'setup',
    'public',
    'audio',
    'video',
    'developer',
    'vendor',
    'log',
]
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
    '\\.scala$',
    'README.md',
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
    '(^|/)\\.[^/]+($|/)', // File starting with a dot
    '__init__.py',
    'setup.py',
    'next-env.d.ts',
    'setup',
    'build',
    'entrypoint',
]

export const blacklistedFilter = [
    '(^|/)\\.[^/]+($|/)', // File starting with a dot
    '__pycache__',
    '_deps',
    'appimage',
    'assets',
    'audio',
    'build',
    'cache',
    'changelog',
    'cmake',
    'cmakefiles',
    'contrib',
    'debug',
    'developer',
    'docker',
    'docs',
    'example',
    'image',
    'img',
    'node_modules',
    'output',
    'public',
    'release',
    'requirements',
    'scripts',
    'setup',
    'target',
    'temp',
    'third_party',
    'tmp',
    'vendor',
    'video',
    'workflows',
    'locale',
    'conf',
    'tutorial',
]
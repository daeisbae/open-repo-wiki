/**
 * Filter the files based on the regex patterns
 * @param {Array<string>} files - The files to filter (Provided by fetchGithubRepoTree)
 * @param {Array<string>} regexFilter - The regex patterns to filter the files
 * @returns {Array<string>} - The filtered files (files that do NOT match the patterns)
 */
export function filterFile(files, regexFilter) {
    const filterPatterns = regexFilter.map((pattern) => new RegExp(pattern));
    return files.filter((file) =>
        !filterPatterns.some((pattern) => pattern.test(file)) // Negate the match
    );
}

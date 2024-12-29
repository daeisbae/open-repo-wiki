import { FullFolder, FullRepository } from '@/service/get-db'

export function formatToMarkdown(fullRepo: FullRepository): string {
    const repo = fullRepo.repository
    const branches = fullRepo.branch
    const folders = fullRepo.folders

    const url = `https://github.com/${repo.owner}/${repo.repo}/blob/${branches?.last_commit_sha}`

    let markdown = recursiveFolderToMarkdown(folders[0], url, '#')

    return markdown
}

function recursiveFolderToMarkdown(
    folder: FullFolder,
    url: string,
    subfolderHeading: string
): string {
    let markdown = `${subfolderHeading} ${folder.usage}\n `
    markdown += `---\n`
    markdown += folder.path
        ? `- Reference: [\`${folder.path}\`](${url}/${folder.path}) \n`
        : ''
    markdown += `\n${folder.ai_summary}\n`
    folder.files.forEach((file) => {
        markdown += `###### ${file.usage}\n`
        markdown += `---\n`
        markdown += file.name
            ? `- Reference: [\`${file.name}\`](${url}/${file.name}) \n`
            : ''
        markdown += `\n${file.ai_summary}\n`
    })
    folder.subfolders.forEach((subfolder) => {
        markdown += recursiveFolderToMarkdown(
            subfolder,
            url,
            subfolderHeading.length >= 5
                ? subfolderHeading
                : subfolderHeading + '#'
        )
    })
    return markdown
}

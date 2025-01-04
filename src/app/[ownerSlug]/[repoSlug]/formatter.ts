import { FileData } from '@/db/models/file'
import { FullFolder, FullRepository } from '@/service/get-db'

export function formatToMarkdownSections(fullRepo: FullRepository): string[] {
    const repo = fullRepo.repository
    const branches = fullRepo.branch
    const folders = fullRepo.folders

    const url = `https://github.com/${repo.owner}/${repo.repo}/blob/${branches?.last_commit_sha}`

    const sections: string[] = []
    if (folders.length > 0) {
        recursiveFolderToMarkdownSections(folders[0], url, 1, sections)
    }

    return sections
}

function recursiveFolderToMarkdownSections(
    folder: FullFolder,
    url: string,
    subfolderHeadingNo: number,
    sections: string[]
) {
    let markdown = `<CollapsibleHeader heading="${folder.usage}" level={${subfolderHeadingNo}} open={true}>\n`
    markdown += `---\n`
    markdown += folder.path
        ? `- Reference: [\`${folder.path}\`](${url}/${folder.path}) \n`
        : ''
    markdown += `\n${folder.ai_summary}\n`

    folder.files.filter(isNotMarkdownFile).forEach((file) => {
        markdown += `<CollapsibleHeader heading="${file.usage}" level={6}>\n`
        markdown += `---\n`
        markdown += file.name
            ? `- Reference: [\`${file.name}\`](${url}/${file.name}) \n`
            : ''
        markdown += `\n${file.ai_summary}\n`
        markdown += `</CollapsibleHeader>\n`
    })
    markdown += `</CollapsibleHeader>\n`

    sections.push(markdown)

    folder.subfolders.forEach((subfolder) => {
        recursiveFolderToMarkdownSections(
            subfolder,
            url,
            subfolderHeadingNo >= 5 ? subfolderHeadingNo : ++subfolderHeadingNo,
            sections
        )
    })
}

function isNotMarkdownFile(file: FileData): boolean {
    return !file.name.includes('.md')
}
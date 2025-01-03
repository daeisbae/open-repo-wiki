
import { FullFolder, FullRepository } from '@/service/get-db'

export function formatToMarkdownSections(fullRepo: FullRepository): string[] {
    const repo = fullRepo.repository
    const branches = fullRepo.branch
    const folders = fullRepo.folders

    const url = `https://github.com/${repo.owner}/${repo.repo}/blob/${branches?.last_commit_sha}`

    // We'll accumulate our markdown sections in an array
    const sections: string[] = []
    if (folders.length > 0) {
        recursiveFolderToMarkdownSections(folders[0], url, '#', sections)
    }

    return sections
}

function recursiveFolderToMarkdownSections(
    folder: FullFolder,
    url: string,
    subfolderHeading: string,
    sections: string[]
) {
    let markdown = `${subfolderHeading} ${folder.usage}\n`
    markdown += `---\n`
    markdown += folder.path
        ? `- Reference: [\`${folder.path}\`](${url}/${folder.path}) \n`
        : ''
    markdown += `\n${folder.ai_summary}\n`

    // folder.files.filter(isNotMarkdownFile).forEach((file) => {
    //     markdown += `###### ${file.usage}\n`
    //     markdown += `---\n`
    //     markdown += file.name
    //         ? `- Reference: [\`${file.name}\`](${url}/${file.name}) \n`
    //         : ''
    //     markdown += `\n${file.ai_summary}\n`
    // })

    // Each "folder section" is one chunk of markdown
    sections.push(markdown)

    folder.subfolders.forEach((subfolder) => {
        recursiveFolderToMarkdownSections(
            subfolder,
            url,
            subfolderHeading.length >= 5 ? subfolderHeading : subfolderHeading + '#',
            sections
        )
    })
}

// function isNotMarkdownFile(file: FileData): boolean {
//     return !file.name.includes('.md')
// }
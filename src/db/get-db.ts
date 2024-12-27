import { Repository, RepositoryData } from '@/db/models/repository'
import { Branch, BranchData } from '@/db/models/branch'
import { Folder, FolderData } from '@/db/models/folder'
import { File, FileData } from '@/db/models/file'

export interface FullFolder extends FolderData {
    files: FileData[]
    subfolders: FullFolder[]
}

export interface FullRepository {
    repository: RepositoryData
    branch: BranchData | null
    folders: FullFolder[]
}

export class FetchRepoService {
    private repository = new Repository()
    private branch = new Branch()
    private folder = new Folder()
    private file = new File()

    async getFullRepositoryTree(
        owner: string,
        repo: string
    ): Promise<FullRepository | null> {
        const repositoryData = await this.repository.select(owner, repo)

        if (!repositoryData) return null

        const branchData = await this.branch.select(repositoryData.url)
        const folders: FullFolder[] = branchData
            ? await this.getFoldersRecursively(branchData.branch_id, null)
            : []

        // if (!branchData) {
        //     throw new Error('No branch found for the repository')
        // }

        return {
            repository: repositoryData,
            branch: branchData,
            folders,
        }
    }

    private async getFoldersRecursively(
        branchId: number,
        parentFolderId: number | null
    ): Promise<FullFolder[]> {
        const allFolders = await this.folder.select(branchId)
        if (!allFolders) throw new Error('No folders found for the repository')

        const currentLevel = allFolders.filter(
            (f) => f.parent_folder_id === parentFolderId
        )

        const foldersWithChildren: FullFolder[] = []
        for (const folder of currentLevel) {
            const subfolders = await this.getFoldersRecursively(
                branchId,
                folder.folder_id
            )
            const files = await this.file.select(folder.folder_id)
            foldersWithChildren.push({
                ...folder,
                files,
                subfolders,
            })
        }
        return foldersWithChildren
    }
}

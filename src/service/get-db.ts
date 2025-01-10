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

export class GetRepositoryService {
    private repository

    constructor() {
        this.repository = new Repository()
    }

    async getAllRepository(): Promise<RepositoryData[] | null> {
        const allRepositories = await this.repository.selectAll()
        if(!allRepositories) return null
        return allRepositories
    }
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

        const allFolders = await this.folder.select(branchData!.branch_id)
        if (!allFolders) return null

        const folders: FullFolder[] = branchData
            ? await this.getFoldersRecursively(null, allFolders)
            : []

        return {
            repository: repositoryData,
            branch: branchData,
            folders,
        }
    }

    private async getFoldersRecursively(
        parentFolderId: number | null,
        allFolders: FolderData[]
    ): Promise<FullFolder[]> {

        const currentLevel = allFolders.filter(
            (f) => f.parent_folder_id === parentFolderId
        )

        if(currentLevel.length === 0) return []

        const foldersWithChildren: FullFolder[] = []
        for (const folder of currentLevel) {
            const subfolders = await this.getFoldersRecursively(
                folder.folder_id,
                allFolders
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

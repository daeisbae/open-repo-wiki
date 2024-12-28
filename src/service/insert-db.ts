import { Repository, RepositoryData } from '@/db/models/repository'
import { Branch, BranchData } from '@/db/models/branch'
import { Folder, FolderData } from '@/db/models/folder'
import { File, FileData } from '@/db/models/file'
import { fetchGithubRepoFile, fetchGithubRepoDetails, fetchGithubRepoTree, RepoTreeResult  } from '@/github/fetchrepo'
import { whitelistedFilter, whitelistedFile, blacklistedFilter, blacklistedFolder }  from '@/github/filterfile'

export class InsertRepoService {
    private repository: Repository
    private branch: Branch
    private folder: Folder
    private file: File

    constructor() {
        this.repository = new Repository()
        this.branch = new Branch()
        this.folder = new Folder()
        this.file = new File()
    }

    async insertRepository(
        owner: string,
        repo: string,
    ): Promise<RepositoryData | null> {
        const repoDetails = await fetchGithubRepoDetails(owner, repo, true)
        const repositoryData = await this.repository.insert(repoDetails.url, repoDetails.repoOwner, repoDetails.repoName, repoDetails.language, repoDetails.description, repoDetails.defaultBranch, repoDetails.topics, repoDetails.stars, repoDetails.forks)

        if(!repositoryData) {
            console.log(`Repository already exists {owner}/{repo}`)
        }
        
        const sha = repoDetails.sha

        const branchCommit = await this.insertBranch(repoDetails.sha, repoDetails.defaultBranch, repoDetails.url, repoDetails.commitAt)

        const branchId = branchCommit.branch_id

        const tree = await fetchGithubRepoTree(owner, repo, repoDetails.sha, '', true)
        
        await this.recursiveInsertFolder(owner, repo, sha, tree, branchId, null)

        return repositoryData
    }

    private async recursiveInsertFolder(
        owner: string,
        repo: string,
        sha: string,
        tree: RepoTreeResult,
        branchId: number,
        parentFolderId: number | null
    ): Promise<void> {
        const allowedFiles = whitelistedFile(tree.files, whitelistedFilter);

        const allowedFolders = blacklistedFolder(tree.subdirectories, blacklistedFilter);

        if(!allowedFiles.length && !allowedFolders.length) {
            return
        }
        const folderData = await this.insertFolder(tree.path.split('/').pop() || '', tree.path, branchId, parentFolderId)

        for(const file of allowedFiles) {
            console.log(`Inserting file ${file}`)
            await this.insertFile(file, folderData.folder_id, await fetchGithubRepoFile(owner, repo, sha, file, true))
        }
        for(const subfolder of allowedFolders) {
            console.log(`Traversing and Inserting folder ${subfolder.path}`)
            await this.recursiveInsertFolder(owner, repo, sha, subfolder, branchId, folderData.folder_id)
        }
    }

    private async insertBranch(
        sha: string,
        name: string,
        repositoryUrl: string,
        commitAt: Date
    ): Promise<BranchData> {
        const branchData = await this.branch.insert(sha, name, repositoryUrl, commitAt)
        return branchData
    }

    private async insertFolder(
        name: string,
        path: string,
        branchId: number,
        parentFolderId: number | null
    ): Promise<FolderData> {
        const folderData = await this.folder.insert(name, path, branchId, parentFolderId)
        return folderData
    }

    private async insertFile(
        name: string,
        folder_id: number,
        content: string
    ): Promise<FileData> {
        const fileData = await this.file.insert(name, folder_id, content)
        return fileData
    }
}

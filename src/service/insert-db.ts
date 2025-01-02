import { Repository, RepositoryData } from '@/db/models/repository'
import { Branch, BranchData } from '@/db/models/branch'
import { Folder, FolderData } from '@/db/models/folder'
import { File, FileData } from '@/db/models/file'
import { fetchGithubRepoFile, fetchGithubRepoDetails, fetchGithubRepoTree, RepoTreeResult  } from '@/github/fetchrepo'
import { whitelistedFilter, whitelistedFile, blacklistedFilter, blacklistedFolder, blacklistedFiles, blacklistedFile }  from '@/github/filterfile'
import { FolderProcessor, CodeProcessor } from '@/agent/structured-output/index'
import { LLMProvider } from '@/llm/llm-provider'

// The maximum allowance of words to feed LLM
const PROCESSOR_MAX_WORD_LIMIT = 50000

interface RepoFileInfo {
    repoOwner: string
    repoName: string
    commitSha: string
}

interface FolderResult {
    path: string
    summary: string
}

export class InsertRepoService {
    private repository: Repository
    private branch: Branch
    private folder: Folder
    private file: File
    private codeProcessor: CodeProcessor
    private folderProcessor: FolderProcessor
    private repoFileInfo: RepoFileInfo | undefined

    constructor(llm: LLMProvider) {
        this.repository = new Repository()
        this.branch = new Branch()
        this.folder = new Folder()
        this.file = new File()
        this.codeProcessor = new CodeProcessor(llm)
        this.folderProcessor = new FolderProcessor(llm)
    }

    async insertRepository(
        owner: string,
        repo: string,
    ): Promise<RepositoryData | null> {
        const repoDetails = await fetchGithubRepoDetails(owner, repo)
        const repositoryData = await this.repository.insert(repoDetails.url, repoDetails.repoOwner, repoDetails.repoName, repoDetails.language, repoDetails.description, repoDetails.defaultBranch, repoDetails.topics, repoDetails.stars, repoDetails.forks)

        // Do not allow duplicate repositories
        if(!repositoryData) {
            console.log(`Repository already exists {owner}/{repo}`)
            return null
        }
        
        const sha = repoDetails.sha

        const branchCommit = await this.insertBranch(repoDetails.sha, repoDetails.defaultBranch, repoDetails.url, repoDetails.commitAt)

        const branchId = branchCommit.branch_id

        this.repoFileInfo = {
            repoOwner: owner,
            repoName: repo,
            commitSha: sha
        }

        const tree = await fetchGithubRepoTree(owner, repo, repoDetails.sha, '')
        
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
    ): Promise<FolderResult | null> {
        let allowedFiles = whitelistedFile(tree.files, whitelistedFilter);
        allowedFiles = blacklistedFiles(allowedFiles, blacklistedFile);

        const allowedFolders = blacklistedFolder(tree.subdirectories, blacklistedFilter);

        if(!allowedFiles.length && !allowedFolders.length) {
            return null
        }
        const folderData = await this.insertFolder(tree.path.split('/').pop() || '', tree.path, branchId, parentFolderId)
        const summaries: string[] = []

        for(const file of allowedFiles) {
            console.log(`Inserting file ${file}`)
            
            const insertedFile = await this.insertFile(file, folderData.folder_id, await fetchGithubRepoFile(owner, repo, sha, file))
            if(!insertedFile) {
                console.warn(`Failed to insert file ${file}`)
                continue
            }

            const fileSummary = `Summary of file ${insertedFile.name}:\n${insertedFile.ai_summary}\n\n`
            summaries.push(fileSummary)
        }
        for(const subfolder of allowedFolders) {
            console.log(`Traversing and Inserting folder ${subfolder.path}`)
            const childFolder = await this.recursiveInsertFolder(owner, repo, sha, subfolder, branchId, folderData.folder_id)
            const folderSummary = `Summary of folder ${subfolder.path}:\n${childFolder?.summary}\n\n`
            summaries.push(folderSummary)
        }

        const aiSummary = await this.folderProcessor.generate(summaries, {...this.repoFileInfo!, path: folderData.path}, PROCESSOR_MAX_WORD_LIMIT)
        if(!aiSummary) {
            console.warn(`Failed to generate AI summary for folder ${folderData.path}`)
            return null
        }
        const {path, ai_summary} = await this.folder.update(aiSummary.summary, aiSummary.usage, folderData.folder_id)
        return {path, summary: ai_summary!}
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
    ): Promise<FileData | null> {
        const aiSummary = await this.codeProcessor.generate(content, {...this.repoFileInfo!, path: name}, PROCESSOR_MAX_WORD_LIMIT)
        if(!aiSummary) {
            console.warn(`Failed to generate AI summary for file ${name}`)
            return null
        }

        const createdFile = await this.file.insert(name, folder_id, content, aiSummary.summary, aiSummary.usage)
        if(!this.repoFileInfo) {
            console.warn(`RepoFileInfo is not set`)
            return null
        }

        return createdFile
    }
}

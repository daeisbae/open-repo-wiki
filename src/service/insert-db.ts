import { Repository, RepositoryData } from '@/db/models/repository'
import { Branch, BranchData } from '@/db/models/branch'
import { Folder, FolderData } from '@/db/models/folder'
import { File, FileData } from '@/db/models/file'
import { fetchGithubRepoFile, fetchGithubRepoDetails, fetchGithubRepoTree, RepoTreeResult  } from '@/github/fetchrepo'
import { whitelistedFilter, whitelistedFile, blacklistedFilter, blacklistedFolder, blacklistedFiles, blacklistedFile }  from '@/github/filterfile'
import { FolderProcessor, CodeProcessor } from '@/agent/structured-output/index'
import { LLMProvider } from '@/llm/llm-provider'

// The maximum allowance of words to feed LLM
const PROCESSOR_MAX_WORD_LIMIT = 45000

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
            console.log(`Repository already exists ${owner}/${repo}`)
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

        const fetchPromises = allowedFiles.map(async (file) => {
            const fileContent = await fetchGithubRepoFile(owner, repo, sha, file);
            return { file, content: fileContent };
        });


        const fileContents = await Promise.all(fetchPromises);

        const fileInsertPromises = fileContents.map(async (fileObj) => {
            const { file, content } = fileObj;
            console.log(`Inserting file ${file}`);

            const insertedFile = await this.insertFile(file, folderData.folder_id, content);
            if (!insertedFile) {
                console.error(`Failed to insert file ${file}`);
                return null;
            }

            return `Summary of file ${insertedFile.name}:\n${insertedFile.ai_summary}\n\n`;
        });

        const folderInsertPromises = allowedFolders.map(async (subfolder) => {
            console.log(`Traversing and inserting folder ${subfolder.path}`);
            const childFolder = await this.recursiveInsertFolder(
                owner,
                repo,
                sha,
                subfolder,
                branchId,
                folderData.folder_id
            );

            if (childFolder?.summary) {
                return `Summary of folder ${subfolder.path}:\n${childFolder.summary}\n\n`;
            }
            return null;
        });

        const [fileSummaries, folderSummaries] = await Promise.all([
            Promise.all(fileInsertPromises),
            Promise.all(folderInsertPromises),
        ]);

        summaries.push(...(fileSummaries.filter(Boolean) as string[]));
        summaries.push(...(folderSummaries.filter(Boolean) as string[]));

        let aiSummary: FolderSummaryOutput | null = null;
        try {
            aiSummary = await this.folderProcessor.generate(summaries, {
                ...this.repoFileInfo!,
                path: folderData.path
            }, PROCESSOR_MAX_WORD_LIMIT)
        } catch (error) {
            aiSummary = null;
        }

        if(!aiSummary) {
            console.error(`Failed to generate AI summary for folder ${folderData.path}`)
            await this.folder.delete(folderData.folder_id)
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
        let aiSummary: {summary: string, usage: string} | null
        try {
            aiSummary = await this.codeProcessor.generate(content, {...this.repoFileInfo!, path: name}, PROCESSOR_MAX_WORD_LIMIT)
        } catch (err) {
            console.warn(`Failed to generate AI summary for file ${name}`)
            return null
        }
        if(!aiSummary) {
            console.error(`Failed to generate AI summary for file ${name}`)
            return null
        }

        const createdFile = await this.file.insert(name, folder_id, content, aiSummary.summary, aiSummary.usage)
        if(!this.repoFileInfo) {
            console.error(`RepoFileInfo is not set`)
            return null
        }

        return createdFile
    }
}

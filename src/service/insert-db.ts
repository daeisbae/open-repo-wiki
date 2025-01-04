import { Repository, RepositoryData } from '@/db/models/repository'
import { Branch, BranchData } from '@/db/models/branch'
import { Folder, FolderData } from '@/db/models/folder'
import { File, FileData } from '@/db/models/file'
import { fetchGithubRepoFile, fetchGithubRepoDetails, fetchGithubRepoTree, RepoTreeResult  } from '@/github/fetchrepo'
import { whitelistedFilter, whitelistedFile, blacklistedFilter, blacklistedFolder, blacklistedFiles, blacklistedFile }  from '@/github/filterfile'
import { FolderProcessor, CodeProcessor } from '@/agent/structured-output/index'
import { LLMProvider } from '@/llm/llm-provider'
import { FolderSummaryOutput, CodeSummaryOutput } from '@/agent/structured-output/index'
import { TokenProcessingConfig } from '@/service/config'

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

        const tree = await fetchGithubRepoTree(owner, repo, repoDetails.sha)

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
        console.log(`Loading folder ${tree.path.length > 0 ? tree.path : '/'}`);

        let allowedFiles = whitelistedFile(tree.files, whitelistedFilter);
        allowedFiles = blacklistedFiles(allowedFiles, blacklistedFile);

        const allowedFolders = blacklistedFolder(tree.subdirectories, blacklistedFilter);

        if(!allowedFiles.length && !allowedFolders.length) {
            return null
        }
        const folderData = await this.insertFolder(tree.path.split('/').pop() || '', tree.path, branchId, parentFolderId)
        const summaries: string[] = []

        const fetchFilePromises = allowedFiles.map(async (file) => {
            const fileContent = await fetchGithubRepoFile(owner, repo, sha, file);
            return { file, content: fileContent };
        });


        const fetchedFiles = await Promise.all(fetchFilePromises);

        const fetchAIFileSummaryPromises = fetchedFiles.map(async (file) => {
            if(!file.content) {
                console.error(`No content for file ${file.file}`)
                return null
            }
            let aiSummary: CodeSummaryOutput | null = null
            let wordDeduction = 0
            let reducedContent = file.content
            let retries = 0

            while (
              !aiSummary &&
              retries++ < TokenProcessingConfig.maxRetries &&
              TokenProcessingConfig.characterLimit - wordDeduction > 0
            ) {
              try {
                reducedContent = file.content.slice(
                  0,
                  TokenProcessingConfig.characterLimit - wordDeduction
                )
                aiSummary = await this.codeProcessor.generate(
                  reducedContent,
                  { ...this.repoFileInfo!, path: file.file }
                )
              } catch (error) {
                console.warn(
                  `Failed to generate AI summary for file ${file.file} with word limit ${
                    TokenProcessingConfig.characterLimit - wordDeduction
                  }, content length ${reducedContent.length}`
                )
              } finally {
                wordDeduction += TokenProcessingConfig.reduceCharPerRetry
              }
            }

            if (!aiSummary) {
              console.error(`Failed to generate AI summary for file ${file.file}`)
              return null
            }
            return { file: file.file, content: file.content, summary: aiSummary!.summary, usage: aiSummary!.usage }
        });

        const fileContents = await Promise.all(fetchAIFileSummaryPromises);

        for(const fileContent of fileContents) {
            if(!fileContent) {
                continue
            }
            console.log(`Processing file ${fileContent?.file}`)
            const insertedFile = await this.insertFile(fileContent.file, folderData.folder_id, fileContent.content, fileContent.summary, fileContent.usage)
            if(!insertedFile) {
                console.error(`Failed to insert file ${fileContent.file}`)
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

        if(!summaries.length) {
            console.error(`No summaries generated for folder ${folderData.path || '/'}`)
            await this.folder.delete(folderData.folder_id)
            return null
        }

        let aiSummary: FolderSummaryOutput | null = null;
        let totalContentInStr = summaries.join('\n\n')
        let retries = 0
        let summaryDeduction = 0
        while(summaries && !aiSummary && TokenProcessingConfig.characterLimit - summaryDeduction > 0 && retries++ < TokenProcessingConfig.maxRetries) {
            try { 
                let reducedContent = totalContentInStr.slice(0, TokenProcessingConfig.characterLimit - summaryDeduction)
                let summariesCombined = totalContentInStr
                while(reducedContent.length < summariesCombined.length && summaries.length > 0) {
                    // To remove the file summary first
                    summaries.shift()
                    summariesCombined = summaries.join('\n\n')
                }
                if(summaries.length === 0) {
                    console.error(`No summaries left for folder ${folderData.path}`)
                    break
                }
                aiSummary = await this.folderProcessor.generate(summaries, {
                    ...this.repoFileInfo!,
                    path: folderData.path
                })
            } catch (error) {
                console.warn(`Failed to generate AI summary for folder ${folderData.path}`)
            }
            summaryDeduction += TokenProcessingConfig.reduceCharPerRetry
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
        content: string,
        aiSummary: string,
        aiUsage: string
    ): Promise<FileData | null> {
        const createdFile = await this.file.insert(name, folder_id, content, aiSummary, aiUsage)
        if(!this.repoFileInfo) {
            console.error(`RepoFileInfo is not set`)
            return null
        }

        return createdFile
    }
}
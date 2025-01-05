import { Repository, RepositoryData } from '@/db/models/repository'
import { Branch, BranchData } from '@/db/models/branch'
import { Folder, FolderData } from '@/db/models/folder'
import { File, FileData } from '@/db/models/file'
import {
  fetchGithubRepoFile,
  fetchGithubRepoDetails,
  fetchGithubRepoTree,
  RepoTreeResult
} from '@/github/fetchrepo'
import {
  whitelistedFilter,
  whitelistedFile,
  blacklistedFiles,
  blacklistedFile,
  blacklistedFolder,
  blacklistedFilter,
} from '@/github/filterfile'
import {
  FolderProcessor,
  CodeProcessor,
  SummaryOutput
} from '@/agent/structured-output/index'
import { LLMProvider } from '@/llm/llm-provider'
import { TokenProcessingConfig } from '@/service/config'

interface RepoFileInfo {
  repoOwner: string
  repoName: string
  commitSha: string
}

export class InsertRepoService {
  private repository: Repository
  private branch: Branch
  private folder: Folder
  private file: File
  private codeProcessor: CodeProcessor
  private folderProcessor: FolderProcessor

  /**
   * Keeps track of each folder’s DB ID for a given folder path.
   * Allows us to insert files later without repeated lookups.
   */
  private folderPathMap: Map<string, number>

  /**
   * Used for providing context to the LLM during summarization.
   */
  private repoFileInfo: RepoFileInfo | undefined

  constructor(llm: LLMProvider) {
    this.repository = new Repository()
    this.branch = new Branch()
    this.folder = new Folder()
    this.file = new File()
    this.codeProcessor = new CodeProcessor(llm)
    this.folderProcessor = new FolderProcessor(llm)
    this.folderPathMap = new Map<string, number>()
  }

  /**
   * Main entry point: insert a repository (folders, files, summaries) into DB.
   *
   *  1) Fetch repository details
   *  2) Insert repository & branch into DB
   *  3) Fetch entire tree (once)
   *  4) Filter tree in memory
   *  5) Insert folder structure in DB (folders only)
   *  6) Fetch & summarize files in parallel, insert them in DB
   *  7) Summarize folders from the bottom up
   */
  async insertRepository(
    owner: string,
    repo: string
  ): Promise<RepositoryData | null> {
    console.log(`Step 1: Fetching repository details for ${owner}/${repo}...`)
    const repoDetails = await fetchGithubRepoDetails(owner, repo)

    console.log(`Step 2: Inserting repository ${repoDetails.repoOwner}/${repoDetails.repoName} to DB...`)
    const repositoryData = await this.repository.insert(
      repoDetails.url,
      repoDetails.repoOwner,
      repoDetails.repoName,
      repoDetails.language,
      repoDetails.description,
      repoDetails.defaultBranch,
      repoDetails.topics,
      repoDetails.stars,
      repoDetails.forks
    )

    // Avoid inserting duplicate repos
    if (!repositoryData) {
      console.log(`Repository already exists: ${owner}/${repo}`)
      return null
    }

    console.log(`Step 3: Inserting branch ${repoDetails.defaultBranch} into DB...`)
    const branchCommit = await this.insertBranch(
      repoDetails.sha,
      repoDetails.defaultBranch,
      repoDetails.url,
      repoDetails.commitAt
    )
    const branchId = branchCommit.branch_id

    // Store basic info for LLM context
    this.repoFileInfo = {
      repoOwner: owner,
      repoName: repo,
      commitSha: repoDetails.sha
    }

    console.log(`Step 4: Fetching entire repo tree for ${owner}/${repo} @ ${repoDetails.sha}...`)
    const fullTree = await fetchGithubRepoTree(owner, repo, repoDetails.sha)

    console.log(`Step 5: Filtering tree in memory...`)
    const filteredTree = this.filterTree(fullTree)

    console.log(`Step 6: Inserting folder structure into DB...`)
    await this.insertFolders(filteredTree, branchId, null)

    console.log(`Step 7: Fetching and summarizing files in parallel...`)
    await this.fetchAndInsertFiles(filteredTree)

    console.log(`Step 8: Summarizing folders bottom-up...`)
    await this.summarizeFolders(filteredTree)

    console.log(`Done! Inserted and summarized repository ${owner}/${repo} successfully.`)
    return repositoryData
  }

  /**
   * Recursively filter out blacklisted folders and files,
   * and return a pruned `RepoTreeResult`.
   */
  private filterTree(tree: RepoTreeResult): RepoTreeResult {
    // Log for debugging
    console.log(`Filtering tree at path "${tree.path || '/'}"...`)

    // 1) Filter files
    let allowedFiles = whitelistedFile(tree.files, whitelistedFilter)
    allowedFiles = blacklistedFiles(allowedFiles, blacklistedFile)

    // 2) Filter subfolders
    const allowedSubdirs = blacklistedFolder(tree.subdirectories, blacklistedFilter)

    // Recursively prune each subdirectory
    const prunedSubdirs = allowedSubdirs
      .map((subdir) => this.filterTree(subdir))
      .filter((subdir) => {
        // Remove empty subdirs if they contain no files and no child subfolders
        return subdir.files.length > 0 || subdir.subdirectories.length > 0
      })

    return {
      path: tree.path,
      files: allowedFiles,
      subdirectories: prunedSubdirs
    }
  }

  /**
   * Inserts the folder structure (only folders) into the database.
   * Recursively called for subdirectories.
   */
  private async insertFolders(
    tree: RepoTreeResult,
    branchId: number,
    parentFolderId: number | null
  ): Promise<void> {
    const folderName = tree.path.split('/').pop() || '' // If empty, it's root
    const folderPath = tree.path

    console.log(`\tInserting folder "${folderName}" with path "${folderPath}"...`)
    const folderData = await this.insertFolder(
      folderName,
      folderPath,
      branchId,
      parentFolderId
    )

    // Track path -> folderId
    this.folderPathMap.set(folderPath, folderData.folder_id)

    // Recurse for subfolders
    for (const subdir of tree.subdirectories) {
      await this.insertFolders(subdir, branchId, folderData.folder_id)
    }
  }

  /**
   * Gathers all files from the pruned tree, fetches content in parallel,
   * summarizes them, and inserts them into the DB.
   */
  private async fetchAndInsertFiles(rootTree: RepoTreeResult) {
    // 1) Collect all file paths
    const allFilePaths: string[] = []
    const gatherFiles = (tree: RepoTreeResult) => {
      allFilePaths.push(...tree.files)
      tree.subdirectories.forEach((subdir) => gatherFiles(subdir))
    }
    gatherFiles(rootTree)

    console.log(`\tFound ${allFilePaths.length} files to process...`)

    // 2) Fetch file contents in parallel
    console.log(`\tFetching file contents in parallel...`)
    const fetchPromises = allFilePaths.map(async (filePath) => {
      try {
        const content = await fetchGithubRepoFile(
          this.repoFileInfo!.repoOwner,
          this.repoFileInfo!.repoName,
          this.repoFileInfo!.commitSha,
          filePath
        )
        return { filePath, content }
      } catch (error) {
        console.error(`\tFailed fetching file: ${filePath}`, error)
        return { filePath, content: null }
      }
    })
    const fetchedFiles = await Promise.all(fetchPromises)

    // 3) Summarize each file
    console.log(`\tGenerating summaries for files...`)
    const processPromises = fetchedFiles.map(async (f) => {
      if (!f.content) return null

      let aiSummary: SummaryOutput | null = null
      let retries = 0
      let wordDeduction = 0
      let reducedContent = f.content

      while (!aiSummary && retries++ < TokenProcessingConfig.maxRetries) {
        try {
          reducedContent = f.content.slice(
            0,
            TokenProcessingConfig.characterLimit - wordDeduction
          )
          aiSummary = await this.codeProcessor.generate(reducedContent, {
            ...this.repoFileInfo!,
            path: f.filePath
          })
        } catch (err) {
          console.warn(
            `\t[Retry ${retries}] Failed generating summary for "${f.filePath}"`
          )
        } finally {
          wordDeduction += TokenProcessingConfig.reduceCharPerRetry
        }
      }

      if (!aiSummary) {
        console.warn(`\tFailed to summarize file "${f.filePath}" after max retries.`)
      }
      return {
        filePath: f.filePath,
        content: f.content,
        aiSummary
      }
    })
    const processedFiles = await Promise.all(processPromises)

    // 4) Insert file records into DB
    console.log(`\tInserting summarized files into DB...`)
    for (const file of processedFiles) {
      if (!file || !file.aiSummary) continue

      const folderPath = file.filePath.includes('/')
        ? file.filePath.slice(0, file.filePath.lastIndexOf('/'))
        : ''
      const folderId = this.folderPathMap.get(folderPath)
      if (!folderId) {
        console.error(`\tNo folder found for path: "${folderPath}" (file: "${file.filePath}")`)
        continue
      }

      const fileName = file.filePath.split('/').pop() || ''
      console.log(`\t\tInserting file "${fileName}" (path: "${file.filePath}")...`)
      await this.insertFile(
        fileName,
        folderId,
        file.content,
        file.aiSummary.summary,
        file.aiSummary.usage
      )
    }
  }

  /**
   * Recursively summarize folders "bottom-up."
   * Summarize subfolders first, then use their summaries + file summaries to create the current folder’s summary.
   */
  private async summarizeFolders(tree: RepoTreeResult): Promise<string | null> {
    console.log(`Summarizing folder "${tree.path || '/'}"...`)

    // 1) Summarize subfolders first
    const subfoldersSummaries: string[] = []
    for (const subdir of tree.subdirectories) {
      const childSummary = await this.summarizeFolders(subdir)
      if (childSummary) {
        subfoldersSummaries.push(`Summary of folder ${subdir.path}:\n${childSummary}\n`)
      }
    }

    // 2) Gather file summaries from DB for this folder
    const folderId = this.folderPathMap.get(tree.path)
    if (!folderId) {
      console.error(`\tNo folder ID found for path: "${tree.path}"`)
      return null
    }

    const filesInFolder = await this.file.select(folderId)
    const fileSummaries: string[] = filesInFolder.map(
      (f) => `Summary of file ${f.name}:\n${f.ai_summary}\n`
    )

    // If there's nothing to summarize (no subfolder or file summaries), skip
    if (!subfoldersSummaries.length && !fileSummaries.length) {
      console.log(`\tNo summaries found in folder "${tree.path}". Skipping...`)
      return null
    }

    // 3) Combine subfolder + file summaries
    let allSummaries = [...subfoldersSummaries, ...fileSummaries]
    let combined = allSummaries.join('\n\n')

    // 4) Summarize with folderProcessor
    let aiSummary: SummaryOutput | null = null
    let retries = 0
    let summaryDeduction = 0

    while (!aiSummary && retries++ < TokenProcessingConfig.maxRetries) {
      try {
        const reducedContent = combined.slice(
          0,
          TokenProcessingConfig.characterLimit - summaryDeduction
        )
        aiSummary = await this.folderProcessor.generate([reducedContent], {
          ...this.repoFileInfo!,
          path: tree.path
        })
      } catch (error) {
        console.warn(`\t[Retry ${retries}] Failed to summarize folder "${tree.path}"`)
      }
      summaryDeduction += TokenProcessingConfig.reduceCharPerRetry
    }

    if (!aiSummary) {
      console.error(`\tNo AI summary produced for folder "${tree.path}" after max retries.`)
      return null
    }

    // 5) Store the folder summary in DB
    console.log(`\tStoring AI summary for folder "${tree.path}"...`)
    await this.folder.update(aiSummary.summary, aiSummary.usage, folderId)

    // Return summary for parent to build upon
    return aiSummary.summary
  }

  // ---------------------------------------------------------------------------
  // Database Helpers
  // ---------------------------------------------------------------------------

  private async insertBranch(
    sha: string,
    name: string,
    repositoryUrl: string,
    commitAt: Date
  ): Promise<BranchData> {
    return this.branch.insert(sha, name, repositoryUrl, commitAt)
  }

  private async insertFolder(
    name: string,
    path: string,
    branchId: number,
    parentFolderId: number | null
  ): Promise<FolderData> {
    return this.folder.insert(name, path, branchId, parentFolderId)
  }

  private async insertFile(
    name: string,
    folderId: number,
    content: string,
    aiSummary: string,
    aiUsage: string
  ): Promise<FileData | null> {
    return this.file.insert(name, folderId, content, aiSummary, aiUsage)
  }
}
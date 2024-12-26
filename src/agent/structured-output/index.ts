import { LLMProvider } from '@/llm/llm-provider'
import { SchemaParser } from '@/agent/structured-output/schema-parser'
import { getSchema, SchemaType } from '@/agent/structured-output/schema-factory'
import {
    PromptGenerator,
    PromptType,
    RepoInfo,
} from '@/agent/structured-output/prompt-generator'
import { CodePrompt, FolderPrompt } from '@/agent/structured-output/prompt'

/**
 * Abstract base class for processing prompts using LLM
 */
abstract class BaseProcessor {
    protected llm: LLMProvider
    protected schemaParser!: SchemaParser
    protected promptGenerator!: PromptGenerator

    /**
     * Creates a new BaseProcessor instance
     * @param llm - The LLM provider instance to use for processing
     */
    constructor(llm: LLMProvider) {
        this.llm = llm
    }

    /**
     * Process the given prompt using LLM and parse the response into JSON format
     * @param {any} prompt - The prompt to process
     * @param {RepoInfo | null} repoInfo - Information about the repository
     * @returns Parsed object from the LLM response
     */
    protected async process(prompt: any, repoInfo: RepoInfo | null): Promise<object> {
        const response = await this.llm.run(prompt, [])
        return await this.schemaParser.parse(response)
    }
}

/**
 * Processes code-related prompts with specific schema and formatting
 * @example
 * const llm = new GoogleProvider(...)
 * const codeProcessor = new CodeProcessor(llm)
 * const sourceCode = `function add(a: number, b: number): number { return a + b }`
 * const result = await codeProcessor.process(sourceCode)
 */
export class CodeProcessor extends BaseProcessor {
    /**
     * Creates a new CodeProcessor instance with file schema type
     * @param llm - The LLM provider instance
     */
    constructor(llm: LLMProvider) {
        super(llm)
        this.schemaParser = new SchemaParser(getSchema(SchemaType.FILE))
        this.promptGenerator = new PromptGenerator(
            {
                template:
                    'The following instruction is given:\n{requirements}\n{formatInstructions}\n' +
                    'The given repository owner is {repoOwner} with repository name of {repoName}\n' +
                    'The commit SHA referenced is {commitSha}\n' +
                    'The path of the file is {path}\n' +
                    'Below is the code for your task: {code}',
            },
            PromptType.File
        )
    }

    /**
     * Process the given code string
     * @param {string }code - Source code to process
     * @param {RepoInfo} repoInfo - Information about the repository
     * @returns Processed and parsed JSON object defined in schema factory
     */
    async process(code: string, repoInfo: RepoInfo): Promise<object> {
        const prompt = await this.promptGenerator.generate(
            {
                requirements: CodePrompt,
                formatInstructions: this.schemaParser.formalInstructions,
                ...repoInfo,
            },
            code
        )
        return await super.process(prompt, null)
    }
}

/**
 * Processes folder-related prompts with specific schema and formatting
 * @example
 * const llm = new new GoogleProvider(...)
 * const folderProcessor = new FolderProcessor(llm)
 * const folderSummaries = ['{file 1 summary}', '{file 2 summary}']
 * const result = await folderProcessor.process(folderSummaries)
 */
export class FolderProcessor extends BaseProcessor {
    /**
     * Creates a new FolderProcessor instance with folder schema type
     * @param {LLMProvider} llm - The LLM provider instance
     */
    constructor(llm: LLMProvider) {
        super(llm)
        this.schemaParser = new SchemaParser(getSchema(SchemaType.FOLDER))
        this.promptGenerator = new PromptGenerator(
            {
                template:
                    'The following instruction is given:\n{requirements}\n{formatInstructions}\n' +
                    'The given repository owner is {repoOwner} with repository name of {repoName}\n' +
                    'The commit SHA referenced is {commitSha}\n' +
                    'The path of the folder is {path}\n' +
                    'Below are the summaries for the codebase:\n{ai_summaries}',
            },
            PromptType.Folder
        )
    }

    /**
     * Process the given code string
     * @param {Array<string> folder - summaries of files by LLMs
     * @param {RepoInfo} repoInfo - Information about the repository
     * @returns Processed and parsed JSON object defined in schema factory
     */
    async process(folder: string[], repoInfo: RepoInfo): Promise<object> {
        const prompt = await this.promptGenerator.generate(
            {
                requirements: FolderPrompt,
                formatInstructions: this.schemaParser.formalInstructions,
                ...repoInfo
            },
            undefined,
            folder
        )
        return await super.process(prompt, null)
    }
}

import { PromptTemplate } from '@langchain/core/prompts'

/**
 * Configuration interface for PromptTemplate
 * @interface PromptTemplateConfig
 */
export interface PromptTemplateConfig {
    template: string
}

/**
 * Interface for formatting instructions
 * @interface PromptTemplateVariables
 */
export interface BasePromptTemplateVariables extends RepoInfo {
    requirements: string
    formatInstructions: string
}

/**
 * Interface for basic repo module information
 * @interface ModuleInfo
 */
export interface RepoInfo {
    repoOwner: string
    repoName: string
    commitSha: string
    path: string
}

/**
 * Interface for formatting instructions
 * @interface PromptTemplateVariables
 */
export interface FilePromptTemplateVariables
    extends BasePromptTemplateVariables {
    code: string
}

/**
 * Interface for formatting instructions
 * @interface PromptTemplateVariables
 */
export interface FolderPromptTemplateVariables
    extends BasePromptTemplateVariables {
    ai_summaries: string
}

/**
 * Enum defining types of prompts that can be generated
 * @enum {string}
 */
export enum PromptType {
    Folder = 'folder',
    File = 'file',
}

/**
 * Class responsible for generating prompts based on different PromptTypes
 * @class PromptGenerator
 */
export class PromptGenerator {
    protected prompt: PromptTemplate
    protected promptType: PromptType

    /**
     * Creates an instance of PromptGenerator
     * @example
     * const generator = new PromptGenerator({
     *     template: "The following instruction is given:\n{formatInstructions}\nBelow is the code for your task: {code}",
     *     inputVariables: ["code"],
     *     partialVariables: {
     *         formatInstructions: CodePrompt // Import CodePrompt from prompt.ts
     *     }}, PromptType.File);
     * @example
     * const generator = new PromptGenerator({
     *    template: "The following instruction is given:\n{formatInstructions}\nBelow are the AI summaries for the codebase:\n{ai_summaries}",
     *   inputVariables: ["ai_summaries"],
     *  partialVariables: {
     *     formatInstructions: FolderPrompt // Import FolderPrompt from prompt.ts
     * }}, PromptType.Folder);
     * @param {PromptTemplateConfig} config - Configuration for the prompt template
     * @param {PromptType} promptType - Type of prompt to generate
     */
    constructor(config: PromptTemplateConfig, promptType: PromptType) {
        this.prompt = PromptTemplate.fromTemplate(config.template)
        this.promptType = promptType
    }

    /**
     * Generates a formatted prompt based on the prompt type and inputs
     * @param {string} [code] - Optional code string for file prompts
     * @param {string[]} [ai_summaries] - Optional array of AI summaries for folder prompts
     * @returns {Promise<string>} Formatted prompt string
     * @throws {Error} If prompt type is invalid or required input is missing
     */
    async generate(
        variables: BasePromptTemplateVariables,
        code?: string,
        ai_summaries?: string[]
    ): Promise<string> {
        const promptMap: Record<PromptType, string> = {
            [PromptType.Folder]: ai_summaries?.join('\n') ?? '',
            [PromptType.File]: code ?? '',
        }

        const userPrompt: string = promptMap[this.promptType]
        if (!userPrompt.length) {
            throw new Error(
                'Invalid prompt type or missing input for prompt generation'
            )
        }

        return this.prompt.format(
            this.promptType === PromptType.File
                ? { ...variables, code: userPrompt }
                : { ...variables, ai_summaries: userPrompt }
        )
    }
}

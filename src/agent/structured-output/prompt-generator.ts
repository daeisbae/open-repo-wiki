import { PromptTemplate } from '@langchain/prompts'

/**
 * Configuration interface for PromptTemplate
 * @interface PromptTemplateConfig
 */
export interface PromptTemplateConfig {
    template: string
    inputVariables: string[]
    partialVariables: Instruction
}

/**
 * Interface for formatting instructions
 * @interface Instruction
 */
export interface Instruction {
    formatInstructions: string
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
    protected template: PromptTemplate
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
        this.template = new PromptTemplate({
            ...config,
        })
        this.promptType = promptType
    }

    /**
     * Generates a formatted prompt based on the prompt type and inputs
     * @param {string} [code] - Optional code string for file prompts
     * @param {string[]} [ai_summaries] - Optional array of AI summaries for folder prompts
     * @returns {Promise<string>} Formatted prompt string
     * @throws {Error} If prompt type is invalid or required input is missing
     */
    async generate(code?: string, ai_summaries?: string[]): Promise<string> {
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

        return this.template.format( this.promptType === PromptType.File ? { code: userPrompt } : { ai_summaries: userPrompt }) 
    }
}

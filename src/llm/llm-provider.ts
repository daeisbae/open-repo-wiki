import LLMConfig from '@/llm/llm-config'

/**
 * Represents a single message in the conversation history.
 */
export interface HistoryItem {
    role: string
    parts: { text: string }[]
}

/**
 * Abstract class for LLM providers (e.g. OpenAI, Gemini, etc.)
 * @abstract
 * @class LLMProvider
 */
export abstract class LLMProvider {
    /**
     * Constructor for LLMProvider
     * @param {string} apikey - API key for the LLM service (your secret key)
     * @param {string} modelName - Model identifier (e.g. gemini-1.5-pro)
     * @param {LLMConfig} llmConfig - Configuration for LLM
     * @param {string} systemPrompt - System prompt for the LLM
     */
    constructor(
        protected apikey: string,
        protected modelName: string,
        protected llmConfig: LLMConfig,
        protected systemPrompt?: string
    ) {
        this.apikey = apikey
        this.modelName = modelName
        this.llmConfig = llmConfig
        this.systemPrompt = systemPrompt
    }

    /**
     * Executes the LLM with given prompt
     * @abstract
     * @param {string} userPrompt - User input prompt (The code will go inside here)
     * @param {Array<{ role: string; parts: Array<{ text: string }> }>} history - The history of the conversation
     * @throws {Error} When not implemented by child class
     * @returns {Promise<any>} The LLM response
     */
    async run(userPrompt: string, history: HistoryItem[]): Promise<any> {
        throw new Error('The LLM chat method run() must be implemented')
    }
}

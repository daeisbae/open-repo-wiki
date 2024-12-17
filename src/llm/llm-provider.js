import LLMConfig from '@/llm/llmconfig.js'

/**
 * Abstract class for LLM providers (e.g. OpenAI, Gemini, etc.)
 * @abstract
 * @class LLMProvider
 */
export default class LLMProvider {
    /**
     * Constructor for LLMProvider
     * @param {string} apikey - API key for the LLM service (your secret key)
     * @param {string} model - Model identifier (e.g. gemini-1.5-pro)
     * @param {LLMConfig} llmconfig - Configuration for LLM
     * @param {string} systemPrompt - System prompt for the LLM
     */
    constructor(apikey, model, llmconfig, systemPrompt) {
        this.apikey = apikey;
        this.model = model;
        this.llmconfig = llmconfig;
        this.systemPrompt = systemPrompt
    }

    /**
     * Executes the LLM with given prompt
     * @abstract
     * @param {string} userPrompt - User input prompt (The code will go inside here)
     * @param {Array<role: string, parts: Array<text: string>>} history - The history of the conversation
     * @throws {Error} When not implemented by child class
     * @returns {Promise<string>} The LLM response
     */
    async run(userPrompt, history) {
        throw new Error('The LLM chat method run() must be implemented');
    }
}
import LLMProvider from '@/llm/llm-provider.js';
import LLMConfig from '@/llm/llm-config.js';
import { GoogleGenerativeAI } from '@google/generative-ai';

/**
 * Class for Google Gemini LLM
 * @class GoogleProvider
 */
class GoogleProvider extends LLMProvider {
    /**
     * Constructor for Google Gemini LLM
     * @param {string} apiKey - API key for google ai studio (https://aistudio.google.com)
     * @param {string} modelName - Select model available in google ai studio
     * @param {LLMConfig} llmconfig - Configuration for LLM
     * @param {string} systemPrompt - System prompt for the LLM
     */
    constructor(apiKey, modelName, llmconfig, systemPrompt) {
        super(apiKey, modelName, llmconfig, systemPrompt);
        this.llm = new GoogleGenerativeAI({ apiKey: apiKey, systemInstruction: systemPrompt, model: modelName });

        this.config = {
            temperature: llmconfig.temperature,
            topP: llmconfig.topP,
            topK: llmconfig.topK,
            maxOutputTokens: llmconfig.maxOutputTokens,
            responseMimeType: "text/plain",
        }
    }

    /**
     * Executes the LLM with given prompt
     * @param {string} userPrompt - User input prompt (The code will go inside here)
     * @param {Array<role: string, parts: Array<text: string>>} history - The history of the conversation
     * @returns {Promise<string>} The LLM response
     */
    async run(userPrompt, history) {
        const chatSession = this.llm.startChat({
           ...this.config,
           history: history
        });
        return await chatSession.sendMessage(userPrompt);
    }
}

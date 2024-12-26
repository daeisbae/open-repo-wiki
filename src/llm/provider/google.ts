import { LLMProvider, HistoryItem } from '@/llm/llm-provider'
import LLMConfig from '@/llm/llm-config'
import {
    GenerateContentResult,
    GenerativeModel,
    GoogleGenerativeAI,
} from '@google/generative-ai'

/**
 * Class for Google Gemini LLM
 * @class GoogleProvider
 */
export default class GoogleProvider extends LLMProvider {
    private llm: GoogleGenerativeAI
    private config: {
        temperature: number
        topP: number
        topK: number
        maxOutputTokens: number
        responseMimeType: string
    }
    private model: GenerativeModel

    /**
     * Constructor for Google Gemini LLM
     * @param {string} apiKey - API key for google ai studio (https://aistudio.google.com)
     * @param {string} modelName - Select model available in google ai studio
     * @param {LLMConfig} llmconfig - Configuration for LLM
     * @param {string} systemPrompt - System prompt for the LLM
     */
    constructor(
        apiKey: string,
        modelName: string,
        llmconfig: LLMConfig,
        systemPrompt?: string
    ) {
        super(apiKey, modelName, llmconfig, systemPrompt)
        this.llm = new GoogleGenerativeAI(this.apikey)
        this.model = this.llm.getGenerativeModel({ model: this.modelName })

        this.config = {
            temperature: this.llmConfig.temperature,
            topP: this.llmConfig.topP,
            topK: this.llmConfig.topK,
            maxOutputTokens: this.llmConfig.maxToken,
            responseMimeType: 'text/plain',
        }
    }

    /**
     * Executes the LLM with given prompt
     * @param {string} userPrompt - User input prompt (The code will go inside here)
     * @param {Array<role: string, parts: Array<text: string>>} history - The history of the conversation
     * @returns {Promise<String>} The LLM response
     */
    async run(userPrompt: string, history: HistoryItem[]): Promise<String> {
        const chatSession = this.model.startChat({
            ...this.config,
            history: history,
        })
        const data = await chatSession.sendMessage(userPrompt)
        return data.response.text()
    }
}

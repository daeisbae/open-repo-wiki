import { LLMProvider } from '@/llm/llm-provider'
import LLMConfig from '@/llm/llm-config'
import OpenAI from 'openai'

export default class DeepSeekProvider extends LLMProvider {
    private llm: OpenAI
    private config: {
        temperature: number
        maxTokens: number
        timeout: number
        maxRetries: number
        apiKey: string
    }

    /**
     * Constructor for OpenAI LLM
     * @param {string} apiKey - API key for OpenAI
     * @param {string} modelName - Model identifier (e.g. deepseek-chat)
     * @param {LLMConfig} llmConfig - Configuration for LLM
     */
    constructor(apiKey: string, modelName: string, llmConfig: LLMConfig) {
        super(apiKey, modelName, llmConfig, '')
        this.llm = new OpenAI({
            apiKey: apiKey,
            baseURL: 'https://api.deepseek.com',
        })

        this.config = {
            temperature: llmConfig.temperature,
            maxTokens: llmConfig.maxToken,
            timeout: 60,
            maxRetries: 2,
            apiKey: apiKey,
        }
    }

    /**
     * Executes the LLM with given prompt
     * @param {string} userPrompt - User input prompt (The code will go inside here)
     * @returns {Promise<String>} The LLM response
     */
    async run(userPrompt: string): Promise<String> {
        const completion = await this.llm.chat.completions.create({
            model: this.modelName,
            max_tokens: this.llmConfig.maxToken,
            top_p: this.llmConfig.topP,
            temperature: this.llmConfig.temperature,
            messages: [
                {
                    role: 'system',
                    content: userPrompt,
                },
            ],
        })
        return completion.choices[0].message.content!
    }
}

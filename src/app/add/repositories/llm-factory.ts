import { LLMProvider } from '@/llm/llm-provider'
import DeepSeekProvider from '@/llm/provider/deepseek'
import GoogleProvider from '@/llm/provider/google'
import LLMConfig from '@/llm/llm-config'
import dotenv from 'dotenv'
dotenv.config()

/**
 * Factory for creating LLM providers
 */
export default class LLMFactory {
    /**
     * Creates a new LLM provider based on the given provider name
     * @param {LLMConfig} llmConfig - Configuration for the LLM
     * @returns {LLMProvider} The LLM provider instance
     */
    static createProvider(llmConfig: LLMConfig): LLMProvider {
        const provider = process.env.LLM_PROVIDER
        const apiKey = process.env.LLM_APIKEY
        const modelName = process.env.LLM_MODELNAME

        switch (provider) {
            case 'google':
                return new GoogleProvider(apiKey!, modelName!, llmConfig)
            case 'deepseek':
                return new DeepSeekProvider(apiKey!, modelName!, llmConfig)
            default:
                throw new Error(`Unsupported LLM provider: ${provider}`)
        }
    }
}

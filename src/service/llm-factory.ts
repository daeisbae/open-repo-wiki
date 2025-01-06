import { LLMProvider } from '@/llm/llm-provider'
import DeepSeekProvider from '@/llm/provider/deepseek'
import GoogleProvider from '@/llm/provider/google'
import LLMConfig from '@/llm/llm-config'
import dotenv from 'dotenv'
import { OllamaProvider } from '@/llm/provider/ollama'
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

        if (!provider) {
            throw new Error('LLM Provider is not specified. Please set LLM_PROVIDER in the environment\nExample: LLM_PROVIDER=google, LLM_PROVIDER=deepseek, LLM_PROVIDER=ollama')
        }

        if(!modelName) {
            throw new Error('LLM Model name is not specified. Example: LLM_MODELNAME=llama3.3 for llama3.3')
        }

        switch (provider) {
            case 'google':
                return new GoogleProvider(apiKey!, modelName!, llmConfig)
            case 'deepseek':
                return new DeepSeekProvider(apiKey!, modelName!, llmConfig)
            case 'ollama':
                return new OllamaProvider(modelName!, llmConfig)
            default:
                throw new Error(`Unsupported LLM provider: ${provider}`)
        }
    }
}

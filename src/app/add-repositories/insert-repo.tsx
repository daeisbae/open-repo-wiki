'use server'

import LLMConfig from '@/llm/llm-config'
import LLMFactory from '@/app/add-repositories/llm-factory'
import { InsertRepoService } from '@/service/insert-db'

export async function insertRepository(owner: string, repo: string) {
    const llmConfig = new LLMConfig(1, 0.95, 40, 8192)
    const insertRepoService = new InsertRepoService(LLMFactory.createProvider(llmConfig))
    const result = await insertRepoService.insertRepository(owner, repo)
    if (!result) {
        return { success: false, error: 'Repository already exists' }
    }
    return { success: true }
}

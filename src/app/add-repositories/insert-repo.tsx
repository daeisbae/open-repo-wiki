'use server'

import { InsertRepoService } from '@/service/insert-db'

export async function insertRepository(owner: string, repo: string) {
    const insertRepoService = new InsertRepoService()
    const result = await insertRepoService.insertRepository(owner, repo)
    if (!result) {
        return { success: false, error: 'Repository already exists' }
    }
    return { success: true }
}

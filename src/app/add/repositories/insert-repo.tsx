import InsertQueue from '@/service/insert-queue'

export async function insertRepository(owner: string, repo: string) {
    const queue = InsertQueue.getInstance()
    const result = await queue.add({ owner, repo })
    if (!result) {
        return { success: false, error: 'Repository already in queue or invalid. Else wiki generation queue maybe full' }
    }
    return { success: true }
}

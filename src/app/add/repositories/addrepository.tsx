import InsertQueue from "@/service/insert-queue";

export async function addRepository(owner: string, repo: string) {
  if (!owner || !repo) {
    return { success: false, error: 'Both owner and repository names are required.' };
  }

  const insertQueue = InsertQueue.getInstance()
  return await insertQueue.add({owner, repo});
}
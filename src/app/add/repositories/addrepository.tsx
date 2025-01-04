import InsertQueue from "@/service/insert-queue";

export async function addRepository(formData: FormData) {
  const owner: string = formData.get('owner') as string;
  const repo: string = formData.get('repo') as string;

  if (!owner || !repo) {
    return { success: false, error: 'Both owner and repository names are required.' };
  }

  const insertQueue = InsertQueue.getInstance()
  return await insertQueue.add({owner, repo});
}
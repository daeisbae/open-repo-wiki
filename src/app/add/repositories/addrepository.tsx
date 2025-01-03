'use server';

import InsertQueue from "@/service/insert-queue";
import React from "react";

export async function addRepository(formData: React.FormData) {
  const owner: string = formData.get('owner') as string;
  const repo: string = formData.get('repo') as string;

  if (!owner || !repo) {
    return { success: false, error: 'Both owner and repository names are required.' };
  }

  const insertRepo = InsertQueue.getInstance()
  return await insertRepo.add({owner, repo});
}
import { NextRequest, NextResponse } from 'next/server';
import { GetRepositoryService } from '@/service/get-db';
import { APIEndpoint } from '@/app/config/config';

export async function GET(request: NextRequest) {
  const repoService = new GetRepositoryService();
  const repos = await repoService.getAllRepository();
  if (!repos) {
    return NextResponse.json(
      { success: false, error: 'No repositories found' },
      { status: 404 }
    );
  }
  return NextResponse.json(repos);
}

export async function POST(request: NextRequest) {
  const { owner, repo } = await request.json();
  const repoQueue = await fetch(`${APIEndpoint}/api/queue`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ owner, repo }),
  });
  const response = await repoQueue.json();
  return NextResponse.json(response);
}
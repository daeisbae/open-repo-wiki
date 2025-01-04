import { NextRequest, NextResponse } from 'next/server';
import InsertQueue from '@/service/insert-queue';
import { GetRepositoryService } from '@/service/get-db';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { owner, repo } = body;

    if (!owner || !repo) {
      return NextResponse.json(
        { success: false, error: 'Owner and repo are required' },
        { status: 400 }
      );
    }

    const queue = InsertQueue.getInstance();
    const result = await queue.add({ owner, repo });

    if (!result.success) {
      return NextResponse.json(
        result,
        { status: 400 }
      );
    }

    return NextResponse.json(
      result,
      { status: 200 }
    );
  } catch (error) {
    console.error('Error processing repository:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

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
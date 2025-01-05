import InsertQueue from "@/service/insert-queue";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
	const insertQueue = InsertQueue.getInstance();
	const processing = insertQueue.processingItem;
	const processingTime = insertQueue.processingTime;
	const queue = insertQueue.queue;
	if (processing || queue.length > 0) {
		return NextResponse.json({
			status: 200,
			body: {
				processing,
				queue,
				processingTime,
			},
		});
	}
	if (processing || queue.length == 0) {
		return NextResponse.json({
			status: 200,
			body: {
				processing,
				processingTime,
			},
		});
	}
	return NextResponse.json({ error: "No repositories found" }, { status: 404 });
}

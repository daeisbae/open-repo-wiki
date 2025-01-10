import { APIEndpoint } from "@/app/config/config";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
	const queue = await fetch(`${APIEndpoint}/api/queue`);

	return NextResponse.json(await queue.json());
}

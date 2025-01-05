'use client';

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import React, { useState, useEffect } from "react";

interface ProcessingItemProps {
	owner: string;
	repo: string;
	createdAt: string;
}

export default function ProcessingItem({
	owner,
	repo,
	createdAt,
}: ProcessingItemProps) {
	const [elapsedTime, setElapsedTime] = useState(
		calculateElapsedTime(createdAt),
	);

	useEffect(() => {
		const interval = setInterval(() => {
			setElapsedTime(calculateElapsedTime(createdAt));
		}, 1000);

		return () => clearInterval(interval);
	}, [createdAt]);

	return (
		<div>
			<Card>
				<CardHeader>
					<CardTitle>
						{owner}/{repo}
					</CardTitle>
				</CardHeader>
				<CardContent>
					<p className="text-sm text-muted-foreground mb-4">
						Processing this item for: {elapsedTime}
					</p>
				</CardContent>
			</Card>
		</div>
	);
}

function calculateElapsedTime(createdAt: string): string {
	const now = Date.now();
	const createdTime = new Date(createdAt).getTime();
	const elapsedTime = now - createdTime;

	const seconds = Math.floor(elapsedTime / 1000);
	const minutes = Math.floor(seconds / 60);
	const hours = Math.floor(minutes / 60);
	const days = Math.floor(hours / 24);

	if (days > 0) return `${days} days`;
	if (hours > 0) return `${hours} hours`;
	if (minutes > 0) return `${minutes} minutes`;
	return `${seconds} seconds`;
}

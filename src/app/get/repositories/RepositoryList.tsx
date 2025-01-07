"use client";

import React, {JSX, useEffect, useState } from "react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import Link from "next/link";
import { GitFork, Star } from "lucide-react";

export default function RepositoryList() {
	const [repositories, setRepositories] = useState<Repository[]>([]);

	useEffect(() => {
		const fetchRepos = async () => {
			const response = await fetch("/api/repository");
			if (!response.ok) {
				return;
			}
			const data = await response.json();
			setRepositories(data);
		};
		fetchRepos();
	}, []);

	return (
		<div>
			{repositories.map((repository) => (
				<AvailableRepositoryCard key={repository.url} repository={repository} />
			))}
		</div>
	)
}

interface Repository {
	owner: string
	repo: string
	description: string
	stars: number
	forks: number
	url: string
}
interface RepositoryProps {
	repository: Repository
}

export function AvailableRepositoryCard({ repository }: RepositoryProps): JSX.Element {
	// @ts-ignore
	return (
		<div key={repository.url} className="p-1">
			<Link href={`/${repository.owner}/${repository.repo}`}>
				<Card>
					<CardHeader>
						<CardTitle>
							{repository.owner}/{repository.repo}
						</CardTitle>
						<CardDescription>{repository.description}</CardDescription>
					</CardHeader>
					<CardContent>
						<div className="flex items-center gap-4 mb-4">
							<div className="flex items-center">
								<Star className="w-4 h-4 mr-1" />
								<span>{repository.stars}</span>
							</div>
							<div className="flex items-center">
								<GitFork className="w-4 h-4 mr-1" />
								<span>{repository.forks}</span>
							</div>
						</div>
					</CardContent>
				</Card>
			</Link>
		</div>
	);
}

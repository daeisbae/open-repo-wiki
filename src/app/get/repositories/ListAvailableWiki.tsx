'use client';

import React, {useEffect, useState, Suspense} from "react";
import Loading from "@/app/get/repositories/loading";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import Link from "next/link";
import { GitFork, Star } from "lucide-react";

export default function ListAvailableWiki() {
    const [repositories, setRepositories] = useState([])

	 useEffect(() => {
        const fetchRepos = async () => {
            const response = await fetch('/api/repository')
            if(!response.ok) {
                return
            }
            const data = await response.json()
            setRepositories(data)
        }
        fetchRepos()
    }, [])

   return (
    <Suspense fallback={<Loading />}>
    <ListWiki repositories={repositories} />
   </Suspense>
   )
}

export function ListWiki({ repositories }) {

	return (
		<div>
			{repositories && repositories.length > 0 && (
				repositories.map((repo) => (
					<div key={repo.url} className="p-1">
						<Link href={`/${repo.owner}/${repo.repo}`}>
							<Card>
								<CardHeader>
									<CardTitle>
										{repo.owner}/{repo.repo}
									</CardTitle>
									<CardDescription>{repo.descriptions}</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="flex items-center gap-4 mb-4">
										<div className="flex items-center">
											<Star className="w-4 h-4 mr-1" />
											<span>{repo.stars}</span>
										</div>
										<div className="flex items-center">
											<GitFork className="w-4 h-4 mr-1" />
											<span>{repo.forks}</span>
										</div>
									</div>
								</CardContent>
							</Card>
						</Link>
					</div>
				)))}
		</div>
	);
}

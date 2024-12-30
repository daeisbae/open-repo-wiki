import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card'
import Link from 'next/link'
import { GitFork, Star } from 'lucide-react'
import { Repository } from '@/db/models/repository'
import React from 'react'

export default async function ListAvailableWiki() {
    const repositories = await new Repository().selectAll()

    return (
        <ul>
            {repositories ? (
                repositories.map((repo) => (
                    <li key={repo.url}>
                        <Link href={`${repo.owner}/${repo.repo}`}>
                            <Card>
                                <CardHeader>
                                    <CardTitle>
                                        {repo.owner}/{repo.repo}
                                    </CardTitle>
                                    <CardDescription>
                                        {repo.descriptions}
                                    </CardDescription>
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
                    </li>
                ))
            ) : (
                <p>No repositories found</p>
            )}
        </ul>
    )
}

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
    try {
        const repositories = await new Repository().selectAll() || [];

        return (
            <div>
                {repositories.length > 0 ? (
                    repositories.map((repo) => (
                        <div key={repo.url} className='p-1'>
                            <Link href={`/${repo.owner}/${repo.repo}`}>
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
                        </div>
                    ))
                ) : (
                    <div className="p-4 text-center">
                        <p>No repositories available at the moment</p>
                    </div>
                )}
            </div>
        )
    } catch (error) {
        console.error('Error fetching repositories:', error);
        return (
            <div className="p-4 text-center">
                <p>Unable to load repositories. Please try again later.</p>
            </div>
        );
    }
}

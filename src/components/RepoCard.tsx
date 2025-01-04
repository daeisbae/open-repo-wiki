import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Star, GitFork } from 'lucide-react'
import React from 'react'

export interface RepoDetails {
    owner: string
    repo: string
    descriptions: string
    stars: number
    forks: number
    url: string
    default_branch: string
    topics: string[]
}

export interface RepoCardProps {
    repoInfo: RepoDetails
}

export function RepoCard({ repoInfo }: RepoCardProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>
                    {repoInfo.owner}/{repoInfo.repo}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                    {repoInfo.descriptions ?? 'No description provided'}
                </p>
                <div className="flex items-center gap-4 mb-4">
                    <div className="flex items-center">
                        <Star className="w-4 h-4 mr-1" />
                        <span>{repoInfo.stars}</span>
                    </div>
                    <div className="flex items-center">
                        <GitFork className="w-4 h-4 mr-1" />
                        <span>{repoInfo.forks}</span>
                    </div>
                </div>
                <a
                    href={repoInfo.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                >
                    View on GitHub
                </a>
                <Separator className="my-4" />
                <div>
                    <h4 className="font-semibold mb-2">Topics</h4>
                    <div className="flex flex-wrap gap-2">
                        {repoInfo.topics.map((topic, index) => (
                            <Badge key={index} variant="secondary">
                                {topic}
                            </Badge>
                        ))}
                        {repoInfo.topics.length === 0 && <p>No topics found</p>}
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

'use client';

import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import Link from 'next/link';
import { GitFork, Star } from 'lucide-react';
import Loading from '@/app/get/repositories/loading';

interface Repository {
    url: string;
    owner: string;
    repo: string;
    descriptions: string;
    stars: number;
    forks: number;
}

export default function ListAvailableWiki() {
    const [repositories, setRepositories] = useState<Repository[] | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchRepositories = async () => {
            try {
                const response = await fetch('/api/repositories/get', {
                    method: 'GET',
                });
                const data = await response.json();

                if (data.success) {
                    setRepositories(data.data);
                } else {
                    setError(data.error || 'Failed to load repositories');
                }
            } catch (err) {
                setError('An error occurred while fetching repositories');
            } finally {
                setLoading(false);
            }
        };

        fetchRepositories();
    }, []);

    if (loading) {
        return (
            <Loading />
        );
    }

    if (error) {
        return (
            <div className="p-4 text-center">
                <p>{error}</p>
            </div>
        );
    }

    return (
        <div>
            {repositories && repositories.length > 0 ? (
                repositories.map((repo) => (
                    <div key={repo.url} className="p-1">
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
    );
}
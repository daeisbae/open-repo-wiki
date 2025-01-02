'use client';

import { useEffect, useState } from 'react';
import { RepoCard } from '@/components/RepoCard';
import { MarkdownContent } from '@/components/MarkdownContent';
import { formatToMarkdown } from '@/app/[ownerSlug]/[repoSlug]/formatter';
import Loading from '@/app/[ownerSlug]/[repoSlug]/loading';

interface RepositorySummarizationContentProps {
    owner: string;
    repo: string;
}

export default function RepositorySummarizationContent({
    owner,
    repo,
}: RepositorySummarizationContentProps) {
    const [repoDetails, setRepoDetails] = useState<any | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchRepoDetails = async () => {
            try {
                const response = await fetch(`/api/repositories/${owner}/${repo}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch repository details');
                }
                const data = await response.json();
                console.log(data);
                setRepoDetails(data);
            } catch (err) {
                setError('Unable to load repository details');
            } finally {
                setLoading(false);
            }
        };

        fetchRepoDetails();
    }, [owner, repo]);

    if (loading) {
        return <Loading />;
    }

    if (error) {
        return <p>{error}</p>;
    }

    if (!repoDetails) {
        return <p>Repository not found</p>;
    }

    return (
        <div className="flex flex-col md:flex-row gap-6">
            <div className="w-full md:w-1/3 md:order-2">
                <RepoCard repoInfo={repoDetails.repository} />
            </div>
            <div className="w-full md:w-2/3 md:order-1">
                <MarkdownContent content={formatToMarkdown(repoDetails)} />
            </div>
        </div>
    );
}
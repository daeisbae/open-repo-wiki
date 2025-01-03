'use client';

import { useEffect, useState } from 'react';
import { RepoCard } from '@/components/RepoCard';
import { MarkdownContent } from '@/components/MarkdownContent';
import { formatToMarkdown } from '@/app/[ownerSlug]/[repoSlug]/formatter';
import Loading from '@/app/[ownerSlug]/[repoSlug]/loading';
import { notFound } from 'next/navigation';

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
                if (response.ok) {
                    const data = await response.json();
                    setRepoDetails(data);
                } else {
                    const validRepo = await fetch(`https://api.github.com/repos/${owner}/${repo}`);
                    if (!validRepo.ok) {
                        setError('Repository does not exist');
                        
                    }
                    notFound();
                }

            } catch (err) {
                setRepoDetails(null);
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
        return <h1>Repository does not exist</h1>;
    }

    if (!repoDetails) {
        return notFound();
    }

    return (
        <div className="flex px-2 overflow-x-hidden flex-col lg:flex-row">
            <div className="w-full lg:w-1/3 lg:order-2 md:pl-6">
                <RepoCard repoInfo={repoDetails.repository} />
            </div>
            <div className="w-full mt-6 lg:w-2/3 lg:order-1">
                <MarkdownContent content={formatToMarkdown(repoDetails)} />
            </div>
        </div>
    );
}
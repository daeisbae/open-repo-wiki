import { RepoCard } from '@/components/RepoCard'
import { FetchRepoService } from '@/service/get-db'
import { MarkdownContent } from '@/components/MarkdownContent'
import { notFound } from 'next/navigation'
import { formatToMarkdown } from '@/app/[ownerSlug]/[repoSlug]/formatter'

interface RepositorySummarizationContentProps {
    owner: string
    repo: string
}

export default async function RepositorySummarizationContent({
    owner,
    repo,
}: RepositorySummarizationContentProps) {
    const fetchRepoService = new FetchRepoService()
    const repoDetails = await fetchRepoService.getFullRepositoryTree(
        owner,
        repo
    )

    if (!repoDetails) {
        notFound()
    }

    return (
        <>
            <div className="flex-1">
                <MarkdownContent content={formatToMarkdown(repoDetails)} />
            </div>
            <div className="w-[300px]">
                <RepoCard repoInfo={repoDetails.repository} />
            </div>
        </>
    )
}

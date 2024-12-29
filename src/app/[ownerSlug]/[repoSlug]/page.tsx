import { JSX, Suspense } from 'react'
import { RepoCard } from '@/components/RepoCard'
import { FetchRepoService } from '@/service/get-db'
import { MarkdownContent } from '@/components/MarkdownContent'
import { notFound } from 'next/navigation'
import { formatToMarkdown } from '@/app/[ownerSlug]/[repoSlug]/formatter'
import Loading from '@/app/[ownerSlug]/[repoSlug]/loading'

// Define the correct page props type for Next.js 13+
interface PageProps {
    params: Promise<{ ownerSlug: string; repoSlug: string }>
}

// Main page component
export default async function Page({
    params,
}: PageProps): Promise<JSX.Element> {
    const { ownerSlug, repoSlug } = await params

    const fetchRepoService = new FetchRepoService()
    const repoDetails = await fetchRepoService.getFullRepositoryTree(
        ownerSlug,
        repoSlug
    )

    if (!repoDetails) {
        notFound()
    }

    return (
        <div className="flex gap-6 p-6">
            <Suspense fallback={<Loading />}>
                <div className="flex-1">
                    <MarkdownContent content={formatToMarkdown(repoDetails)} />
                </div>
                <div className="w-[300px]">
                    <RepoCard repoInfo={repoDetails.repository} />
                </div>
            </Suspense>
        </div>
    )
}

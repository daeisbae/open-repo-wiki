import { JSX, Suspense } from 'react'
import { RepoCard } from '@/components/RepoCard'
import Loading from '@/app/[ownerSlug]/[repoSlug]/loading'
import { FetchRepoService, FullRepository } from '@/db/get-db'
import { notFound } from 'next/navigation'

interface PageProps {
    params: {
        ownerSlug: string
        repoSlug: string
    }
}

export default async function RepoPage({
    params,
}: PageProps): Promise<JSX.Element> {
    const { ownerSlug, repoSlug } = await params
    console.log(ownerSlug, repoSlug)

    const fetchRepoService = new FetchRepoService()
    const repoDetails: FullRepository | null =
        await fetchRepoService.getFullRepositoryTree(ownerSlug, repoSlug)

    if (!repoDetails) {
        console.log('Repo not found')
        notFound()
    }

    return (
        <Suspense fallback={<Loading />}>
            <RepoCard repoInfo={repoDetails.repository} />
        </Suspense>
    )
}

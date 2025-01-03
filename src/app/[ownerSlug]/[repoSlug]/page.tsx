import { JSX, Suspense } from 'react'
import Loading from '@/app/[ownerSlug]/[repoSlug]/loading'
import RepositorySummarizationContent from '@/app/[ownerSlug]/[repoSlug]/contents';

interface PageProps {
    params: Promise<{ ownerSlug: string; repoSlug: string }>
}

export default async function Page({
    params,
}: PageProps): Promise<JSX.Element> {
    const { ownerSlug, repoSlug } = await params



    return (
        <div className="flex gap-6 md:p-6 max-w-full overflow-x-hidden">
            <Suspense fallback={<Loading />}>
                <RepositorySummarizationContent
                    owner={ownerSlug}
                    repo={repoSlug}
                    />
            </ Suspense>
        </div>
    )
}

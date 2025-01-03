import { RepoCard } from '@/components/RepoCard';
import { MarkdownContent } from '@/components/MarkdownContent';
import { formatToMarkdownSections } from '@/app/[ownerSlug]/[repoSlug]/formatter';
import Loading from '@/app/[ownerSlug]/[repoSlug]/loading';
import { notFound } from 'next/navigation';
import { FetchRepoService } from '@/service/get-db';

interface RepositorySummarizationContentProps {
    owner: string;
    repo: string;
}

export default async function RepositorySummarizationContent({
    owner,
    repo,
}: RepositorySummarizationContentProps) {
    const repoService = new FetchRepoService()
    const repoDetails = await repoService.getFullRepositoryTree(owner, repo)
    

    if (!repoDetails) {
        return notFound();
    }

    const markdownSections = formatToMarkdownSections(repoDetails);

    return (
        <div className="flex px-2 overflow-x-hidden flex-col lg:flex-row">
            <div className="w-full lg:w-1/3 lg:order-2 md:pl-6">
                <RepoCard repoInfo={repoDetails.repository} />
            </div>
            <div className="w-full mt-6 lg:w-2/3 lg:order-1 space-y-6">
                {markdownSections.map((section, idx) => (
                    <MarkdownContent key={idx} content={section} />
                ))}
            </div>
        </div>
    );
}
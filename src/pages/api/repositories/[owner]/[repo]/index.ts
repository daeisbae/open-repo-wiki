import { NextApiRequest, NextApiResponse } from 'next';
import { FetchRepoService } from '@/service/get-db';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    const { owner, repo } = req.query;

    if (!owner || !repo || typeof owner !== 'string' || typeof repo !== 'string') {
        return res.status(400).json({ error: 'Invalid owner or repository parameters' });
    }

    try {
        const fetchRepoService = new FetchRepoService();
        const repoDetails = await fetchRepoService.getFullRepositoryTree(owner, repo);

        if (!repoDetails) {
            return res.status(404).json({ error: 'Repository not found' });
        }

        res.status(200).json(repoDetails);
    } catch (error) {
        console.error('Error fetching repository details:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
}
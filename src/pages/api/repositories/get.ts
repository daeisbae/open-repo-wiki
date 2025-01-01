import type { NextApiRequest, NextApiResponse } from 'next';
import { Repository } from '@/db/models/repository';

interface ApiResponse {
    success: boolean;
    data?: any[]; // Replace `any` with your repository schema type
    error?: string;
}

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse<ApiResponse>
) {
    if (req.method === 'GET') {
        try {
            const repositories = await new Repository().selectAll();
            res.status(200).json({ success: true, data: repositories! });
        } catch (error) {
            console.error('Error fetching repositories:', error);
            res.status(500).json({ success: false, error: 'Failed to fetch repositories' });
        }
    } else {
        res.setHeader('Allow', ['GET']);
        res.status(405).json({ success: false, error: `Method ${req.method} Not Allowed` });
    }
}
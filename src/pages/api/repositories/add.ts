import type { NextApiRequest, NextApiResponse } from 'next'
import { insertRepository } from '@/service/insert-repo'

interface ApiResponse {
    success: boolean
    message?: string
    error?: string
}

export default async function handler(req: NextApiRequest, res: NextApiResponse<ApiResponse>) {
    if (req.method === 'POST') {
        const { owner, repo }: { owner?: string; repo?: string } = req.body

        if (!owner || !repo) {
            return res.status(400).json({ success: false, error: 'Missing owner or repository' })
        }

        try {
            const result = await insertRepository(owner, repo)
            if (!result.success) {
                return res.status(500).json({ success: false, error: result.error || 'Failed to process repository' })
            }
            res.status(200).json({ success: true, message: `Repository ${owner}/${repo} loaded into queue` })
        } catch (error) {
            res.status(500).json({ success: false, error: 'Internal server error' })
        }
    } else {
        res.setHeader('Allow', ['POST'])
        res.status(405).end(`Method ${req.method} Not Allowed`)
    }
}
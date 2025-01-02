import dbConn from '@/db/utils/connector'

export interface RepositoryData {
    url: string
    owner: string
    repo: string
    language: string
    descriptions: string
    default_branch: string
    stars: number
    forks: number
    topics: string[]
}

interface TopicResultOutput {
    rows?: { topic_name: string }[]
}

export class Repository {
    async select(owner: string, repo: string): Promise<RepositoryData | null> {
        const queryRepo =
            'SELECT * FROM Repository WHERE owner = $1 AND repo = $2'
        const queryTopics =
            'SELECT topic_name FROM RepositoryTopics WHERE repository_url = $1'

        const repoResult = (await dbConn.query(queryRepo, [owner, repo]))
            .rows[0]
        if (!repoResult) {
            return null
        }
        const topicsResult: TopicResultOutput = await dbConn.query(queryTopics, [repoResult.url])

        return {
            ...repoResult,
            topics: topicsResult.rows!.map((row) => row.topic_name),
        }
    }

    async selectAll(): Promise<RepositoryData[] | null> {
        const queryRepo = 'SELECT * FROM Repository'
        
        const repoResult = await dbConn.query(queryRepo)
        return repoResult.rows
    }

    async insert(
        url: string,
        owner: string,
        repo: string,
        language: string,
        description: string,
        defaultBranch: string,
        topics: string[],
        stars: number,
        forks: number,
    ): Promise<RepositoryData | null> {
        const repoQuery = `
                INSERT INTO Repository (url, owner, repo, language, descriptions, default_branch, stars, forks)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (url) DO NOTHING
                RETURNING *;
            `
        const repoValues = [
            url,
            owner,
            repo,
            language,
            description,
            defaultBranch,
            stars,
            forks,
        ]
        const result = await dbConn.query(repoQuery, repoValues)

        const topicQuery = `
                INSERT INTO Topics (topic_name)
                VALUES ($1)
                ON CONFLICT (topic_name) DO NOTHING;
            `
        const topicRepoQuery = `
                INSERT INTO RepositoryTopics (topic_name, repository_url)
                VALUES ($1, $2)
                ON CONFLICT (topic_name, repository_url) DO NOTHING;
            `

        for (const topic of topics) {
            const topicValues = [topic]
            await dbConn.query(topicQuery, topicValues)
        }

        for (const topic of topics) {
            const topicRepoValues = [topic, url]
            await dbConn.query(topicRepoQuery, topicRepoValues)
        }

        return result.rows[0];
    }
}

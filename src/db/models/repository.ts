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
        const topicsResult = await dbConn.query(queryTopics, [repoResult.url])

        return {
            ...repoResult,
            topics: topicsResult.rows.map((row) => row.topic_name),
        }
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
        forks: number
    ): Promise<void> {
        const repoQuery = `
                INSERT INTO Repository (url, owner, repo, language, descriptions, default_branch, stars, forks)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
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
        await dbConn.query(repoQuery, repoValues)

        const topicQuery = `
                IF NOT EXISTS (SELECT * FROM Topics WHERE topic_name = $1)
                BEGIN
                    INSERT INTO Topics (topic_name)
                    VALUES ($1);
                END;
                INSERT INTO RepositoryTopics (topic_name, repository_url)
                VALUES ($1, $2);
            `
        for (const topic of topics) {
            const topicValues = [topic, url]
            await dbConn.query(topicQuery, topicValues)
        }
    }
}

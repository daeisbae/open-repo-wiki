import dbConn from '@/db/utils/connector'

export interface BranchData {
    branch_id: number
    last_commit_sha: string
    name: string
    repository_url: string
    commit_at: Date
    created_at: Date
    ai_summary: string | null
}

export class Branch {
    async select(repository_url: string): Promise<BranchData | null> {
        const query = 'SELECT * FROM Branch WHERE repository_url = $1'
        const values = [repository_url]
        const result = await dbConn.query(query, values)
        return result.rows[0] || null
    }

    async insert(
        sha: string,
        name: string,
        repository_url: string,
        commit_at: Date
    ): Promise<BranchData> {
        const query = `
            INSERT INTO Branch (last_commit_sha, name, repository_url, commit_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            RETURNING *;
        `
        const values = [sha, name, repository_url, commit_at]
        const result = await dbConn.query(query, values)
        if(result.rowCount === 0) {
            const getBranchQuery = 'SELECT * FROM Branch WHERE repository_url = $1 AND last_commit_sha = $2'
            const getBranchValues = [repository_url, sha]
            const getBranchResult = await dbConn.query(getBranchQuery, getBranchValues)
            return getBranchResult.rows[0]
        }
        return result.rows[0]
    }

    async update(ai_summary: string, branch_id: number): Promise<BranchData> {
        const query = `
            UPDATE Branch 
            SET ai_summary = $1
            WHERE branch_id = $2
            RETURNING *;
        `
        const values = [ai_summary, branch_id]
        const result = await dbConn.query(query, values)
        return result.rows[0]
    }
}

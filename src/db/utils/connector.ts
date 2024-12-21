import { Pool, QueryResult } from 'pg'
import { DBConfig } from '@/db/config/config'

/**
 * Database connection handler (Instance pattern - Although not recommended due to thread issue, this is currently the best solution)
 * @class DatabaseConnector
 */
class DBConnector {
    private pool: Pool

    /**
     * Creates a new database connection pool
     * @constructor
     */
    constructor() {
        this.pool = new Pool(DBConfig)
    }

    /**
     * Executes a parameterized SQL query
     * @param text - SQL query text
     * @param params - Query parameters
     * @returns Results from database query
     * @throws Database query errors
     */
    async query<T = any>(
        text: string,
        params?: any[]
    ): Promise<QueryResult<T>> {
        try {
            return await this.pool.query(text, params)
        } catch (error) {
            throw new Error(
                `Database query failed: ${
                    error instanceof Error ? error.message : 'Unknown error'
                }`
            )
        }
    }
}

export default new DBConnector()

import pg, { QueryResult, QueryResultRow } from 'pg'
import { DBConfig } from '@/db/config/config'
import { promises as fs } from 'fs'

/**
 * Database connection handler (Instance pattern - Although not recommended due to thread issue, this is currently the best solution)
 * @class DatabaseConnector
 */
class DBConnector {
    private pool: pg.Pool
    private conn: boolean
    private static instance: DBConnector

    /**
     * Creates a new database connection pool
     * @constructor
     */
    private constructor() {
        const { Pool } = pg
        this.conn = false
        const { certificate, ...config } = DBConfig
        if (!certificate) {
            this.pool = new Pool(config)
            return
        }
        this.pool = new Pool({
            ...config,
            ssl: {
                rejectUnauthorized: false,
                ca: fs
                    .readFile(process.cwd() + '/certificates/' + certificate)
                    .toString(),
                sslmode: 'require',
            },
        })
    }

    /**
     * Get the instance of the database connector
     * @returns The database connector instance
     */
    static getInstance(): DBConnector {
        if (!DBConnector.instance) {
            DBConnector.instance = new DBConnector()
        }
        return DBConnector.instance
    }

    /**
     * Executes a parameterized SQL query
     * @param text - SQL query text
     * @param params - Query parameters
     * @returns Results from database query
     * @throws Database query errors
     */
    async query<T extends QueryResultRow = any>(
        text: string,
        params?: any[]
    ): Promise<QueryResult<T>> {
        let client: pg.PoolClient | undefined = undefined
        try {
            client = await this.pool.connect()
            this.conn = true
            const result = await this.pool.query(text, params)
            await client.release()
            this.conn = false
            return result
        } catch (error) {
            this.conn && client.release()
            console.log(
                `Database query failed: ${
                    error instanceof Error ? error.message : 'Unknown error'
                }`
            )
        }
    }
}

// eslint-disable-next-line import/no-anonymous-default-export
export default DBConnector.getInstance()

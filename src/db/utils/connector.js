import { Pool } from 'pg';
import DBConfig from '@/db/config/config';

/**
 * Database connection handler (Singleton pattern - Although not recommended due to thread issue, this is currently the best solution)
 * @class DatabaseConnector
 */
class DBConnector {
    /**
     * Creates a new database connection pool
     * @constructor
     */
    constructor() {
        this.pool = new Pool(DBConfig);
    }

    /**
     * Executes a parameterized SQL query
     * @param {string} text - SQL query text
     * @param {Array} params - Query parameters
     * @returns {Promise<QueryResult>} Results from database query
     * @throws {Error} Database query errors
     */
    async query(text, params) {
        return await this.pool.query(text, params);
    }
}

export default new DBConnector();
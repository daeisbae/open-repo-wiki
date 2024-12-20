import pkg from 'pg';
const { Pool } = pkg;
import { DBConfig } from '../config/config.js';
import readline from 'readline';

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

async function confirmDrop() {
    return new Promise((resolve) => {
        rl.question(`🚫  Are you sure you want to drop database '${DBConfig.database}'? (yes/no): `, (answer) => {
            resolve(answer.toLowerCase() === 'yes');
            rl.close();
        });
    });
}

async function dropDatabase() {
    console.log('🔄 Preparing to drop database...');
    
    const confirmed = await confirmDrop();
    if (!confirmed) {
        console.log('❌ Operation cancelled');
        process.exit(0);
    }

    const pgPool = new Pool({
        ...DBConfig,
    });

    try {
        console.log('🔄 Terminating existing connections...');
        await pgPool.query(`
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '${DBConfig.database}'
            AND pid <> pg_backend_pid();
        `);

        console.log('🔄 Dropping database...');
        await pgPool.query(`DROP DATABASE IF EXISTS ${DBConfig.database}`);
        console.log('✅ Database dropped successfully');
    } catch (error) {
        console.error('❌ Failed to drop database:', error.message);
        process.exit(1);
    } finally {
        await pgPool.end();
    }
}

dropDatabase().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
});
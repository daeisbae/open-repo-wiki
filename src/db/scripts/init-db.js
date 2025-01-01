import { createRequire } from 'module'
const require = createRequire(import.meta.url)
const { Client } = require('pg')
const { readFile } = require('fs/promises')
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import { DBConfig } from '../config/config.js'
import { promises as fs } from 'fs'

const __dirname = dirname(fileURLToPath(import.meta.url))

async function initDatabase() {
    console.log('Initializing database with config:', {
        host: DBConfig.host,
        port: DBConfig.port,
        database: DBConfig.database,
        user: DBConfig.user,
    })

    const { certificate, config } = DBConfig

    let pgClient = undefined

    if (!certificate) {
        pgClient = new Client({
            ...config,
        })
    } else {
        pgClient = new Client({
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

    pgClient.connect()

    await pgClient
        .query(`CREATE DATABASE ${DBConfig.database};`)
        .catch((error) => {
            console.log('❌ Database is already created')
        })
        .then(() => {
            console.log('✅ Database created successfully')
        })

    const schemaPath = join(__dirname, '../migrations/create_tables.sql')
    const sql = await readFile(schemaPath, 'utf8')

    await pgClient.query(sql).catch((error) => {
        console.error('❌ Schema loading failed:', error)
    })
    console.log('✅ Schema loaded successfully')
    pgClient.end()
}

initDatabase()
    .then(() => {
        console.log('✅ Database initialization complete')
        process.exit(0)
    })
    .catch((error) => {
        console.error('❌ Fatal error:', error)
        process.exit(1)
    })

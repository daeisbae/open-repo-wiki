import dotenv from 'dotenv'
dotenv.config()

export const DBConfig = {
    host: process.env.DB_HOST,
    port: parseInt(process.env.DB_PORT),
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    certificate: process.env.DB_CERTIFICATE,
}

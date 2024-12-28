import dotenv from 'dotenv'
dotenv.config()


export const GithubAuthConfig = {
    headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` },
}

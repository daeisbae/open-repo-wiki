import axios from 'axios'
import { GithubAuthConfig } from '@/github/config'

axios.defaults.headers.common['Authorization'] =
    GithubAuthConfig.headers.Authorization

interface RateLimit {
    limit: number
    remaining: number
    reset: number
    used: number
    resource: string
}

export async function checkRateLimit(): Promise<RateLimit | null> {
    return await axios
        .get('https://api.github.com/rate_limit')
        .then((res) => res.data.resources.core)
        .catch((error) => {
            console.error(error)
            return null
        })
}

from typing import Optional

import aiohttp
from github.config import github_auth_config

from loguru import logger

async def check_rate_limit() -> Optional[dict]:
    rate_limit_url = 'https://api.github.com/rate_limit'
    async with aiohttp.ClientSession(headers=github_auth_config) as session:
        async with session.get(rate_limit_url, ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                return data['resources']['core']
            else:
                logger.error(f'Error fetching rate limit: {response.status}')
                return None

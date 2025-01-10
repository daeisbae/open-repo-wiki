import os
import dotenv
from loguru import logger
dotenv.load_dotenv()

TokenProcessingConfig = {
    "characterLimit": int(os.getenv('TOKEN_PROCESSING_CHARACTER_LIMIT')), # ~250k tokens
    "maxRetries": int(os.getenv('TOKEN_PROCESSING_MAX_RETRIES')), # 3 retries
    "reduceCharPerRetry": int(os.getenv('TOKEN_PROCESSING_REDUCE_CHAR_PER_RETRY')), # ~50k tokens drop per retry
}

if TokenProcessingConfig['characterLimit'] < TokenProcessingConfig['reduceCharPerRetry']:
    logger.critical('.env: TOKEN_PROCESSING_CHARACTER_LIMIT should be greater than TOKEN_PROCESSING_REDUCE_CHAR_PER_RETRY')
    os.exit(1)

if TokenProcessingConfig['maxRetries'] < 1:
    logger.critical('.env: TOKEN_PROCESSING_MAX_RETRIES should be greater than 0')
    os.exit(1)
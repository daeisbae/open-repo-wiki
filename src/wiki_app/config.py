import os
import sys
import dotenv
from loguru import logger

dotenv.load_dotenv()

TokenProcessingConfig = {
    "characterLimit": int(os.getenv('TOKEN_PROCESSING_CHARACTER_LIMIT', 30000)), 
    "maxRetries": int(os.getenv('TOKEN_PROCESSING_MAX_RETRIES', 3)), 
    "reduceCharPerRetry": int(os.getenv('TOKEN_PROCESSING_REDUCE_CHAR_PER_RETRY', 3000)), 
}

if TokenProcessingConfig['characterLimit'] < TokenProcessingConfig['reduceCharPerRetry']:
    logger.critical('.env: TOKEN_PROCESSING_CHARACTER_LIMIT should be greater than TOKEN_PROCESSING_REDUCE_CHAR_PER_RETRY')
    sys.exit(1)

if TokenProcessingConfig['maxRetries'] < 1:
    logger.critical('.env: TOKEN_PROCESSING_MAX_RETRIES should be greater than 0')
    sys.exit(1)

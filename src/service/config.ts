import dotenv from 'dotenv'
dotenv.config()

export const TokenProcessingConfig = {
    characterLimit: parseInt(process.env.PROCESSOR_CHAR_LIMIT) || 100000, // ~250k tokens
    maxRetries: parseInt(process.env.TOKEN_PROCESSING_MAX_RETRIES) || 3, // 3 retries
    reduceCharPerRetry: parseInt(process.env.TOKEN_PROCESSING_REDUCE_CHAR_PER_RETRY) || 20000, // ~50k tokens drop per retry
}

if(TokenProcessingConfig.characterLimit < TokenProcessingConfig.reduceCharPerRetry) {
    console.error('.env: TOKEN_PROCESSING_CHARACTER_LIMIT should be greater than TOKEN_PROCESSING_REDUCE_CHAR_PER_RETRY')
    process.exit(1)
}

if(TokenProcessingConfig.maxRetries < 1) {
    console.error('.env: TOKEN_PROCESSING_MAX_RETRIES should be greater than 0')
    process.exit(1)
}
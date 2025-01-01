import LLMFactory from '@/app/add/repositories/llm-factory'
import { Repository, RepositoryData } from '@/db/models/repository'
import LLMConfig from '@/llm/llm-config'
import { InsertRepoService } from '@/service/insert-db'
import { checkRateLimit } from '@/github/ratelimit'
import axios from 'axios'

interface InsertItem {
    owner: string
    repo: string
}

export default class InsertQueue {
    private _queue: InsertItem[] = []
    private _isProcessing: boolean = false
    private _repoService: InsertRepoService
    private _processed: InsertItem[] = []
    private static _instance?: InsertQueue
    private _rateLimitBeforeStop: number = 500
    private _maxQueueSize: number = 10
    private _repository: Repository

    private constructor() {
        this._queue = []
        this._isProcessing = false
        this._processed = []
        const llmConfig = new LLMConfig(1, 0.95, 40, 8192)
        this._repoService = new InsertRepoService(
            LLMFactory.createProvider(llmConfig)
        )
        this._repository = new Repository()
    }

    public static getInstance() {
        if (!this._instance) {
            this._instance = new InsertQueue()
        }
        return this._instance
    }

    /**
     * Adds a new item to the queue
     */
    public add(item: InsertItem): boolean {
        // Check if item is already in the queue
        if (this._queue.find((i) => i.owner === item.owner && i.repo === item.repo)) {
            return false
        }

        // Check if item is in the database
        const isIncludedInRepo = this._repository.select(item.owner, item.repo)
        if(isIncludedInRepo == null) {
            return false
        }

        // Check if the queue is full
        if (this._queue.length >= this._maxQueueSize) {
            return false
        }
        
        // Check if the repository exists
        axios.get(`https://api.github.com/repos/${item.owner}/${item.repo}`)
            .then((res) => {
            if (res.status === 404) {
                return false
            }
        })
        
        this._queue.push(item)

        if (!this._isProcessing) {
            this._processQueue()
        }
        return true
    }

    /**
     * Returns the finished queue
     */
    get processed(): InsertItem[] {
        return this._processed
    }

    /**
     * Clears the processed queue
     */
    clearProcessed(): void {
        this._processed = []
    }

    /**
     * Processes the queue, if rate limit is not reached
     * if rate limit is reached, it will wait for the reset time
     */
    private async _processQueue(): Promise<void> {
        this._isProcessing = true
        while (this._queue.length > 0) {
            const rateLimit = await checkRateLimit()
            if (rateLimit?.remaining! < this._rateLimitBeforeStop) {
                console.log('Rate limit reached. Stopping queue processing.')
                const waitTime = rateLimit!.reset - Date.now()
                console.log(`Waiting for ${waitTime}ms`)
                await new Promise((resolve) => setTimeout(resolve, waitTime + 1000))
                continue
            }
            const item = this._queue.shift()
            if (item) {
                await this._processItem(item)
            }
        }
        this._isProcessing = false
    }

    /**
     * Processes an item from the queue
     */
    private async _processItem(
        item: InsertItem
    ): Promise<RepositoryData | null> {
        console.log(`Processing item: ${item}`)
        let result: RepositoryData | null = null
        try {
            result = await this._repoService.insertRepository(
                item.owner,
                item.repo
            )
        } catch (error) {
            console.error(`Failed to process item: ${item}`, error)
        }

        return result
    }

    /**
     * Returns the current queue
     */
    get queue(): InsertItem[] {
        return this._queue
    }
}

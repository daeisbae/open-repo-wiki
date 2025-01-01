'use client'

import React, { useState } from 'react'
import Loading from '@/app/add/repositories/loading'

export default function AddRepository() {
    const [owner, setOwner] = useState<string>('')
    const [repo, setRepo] = useState<string>('')
    const [isLoading, setIsLoading] = useState<boolean>(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault()

        if (!owner || !repo) {
            setError('You need to provide both owner and repository')
            return
        }

        setIsLoading(true)
        setError(null)
        setSuccess(null)

        try {
            const response = await fetch('/api/repositories/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ owner, repo }),
            })

            const result = await response.json()
            if (!result.success) {
                setError(result.error || 'Failed to process repository')
            } else {
                setSuccess(`Repository ${owner}/${repo} loaded into queue`)
            }
        } catch (err) {
            setError('Failed to process repository')
        } finally {
            setIsLoading(false)
            setOwner('')
            setRepo('')
        }
    }

    return (
        <div className="flex flex-col items-center justify-center w-full h-full">
            <h1 className="text-2xl font-bold mb-8">Add Repository</h1>
            <form
                onSubmit={handleSubmit}
                className="flex flex-col gap-4 w-full max-w-md p-6 border rounded-lg shadow-sm"
            >
                <div className="flex flex-col gap-4">
                    <input
                        className="p-4 border rounded-md"
                        type="text"
                        placeholder="Owner"
                        value={owner}
                        onChange={(e) => setOwner(e.target.value)}
                        disabled={isLoading}
                    />
                    <input
                        className="p-4 border rounded-md"
                        type="text"
                        placeholder="Repository"
                        value={repo}
                        onChange={(e) => setRepo(e.target.value)}
                        disabled={isLoading}
                    />
                </div>
                <button
                    type="submit"
                    className="bg-blue-500 hover:bg-blue-600 disabled:opacity-70 text-white font-bold py-4 px-6 rounded-md transition-colors"
                    disabled={isLoading}
                >
                    {isLoading ? <Loading /> : <>Add Repository</>}
                </button>
            </form>
            {success && (
                <div
                    className="p-4 my-4 text-sm text-green-800 rounded-lg bg-green-50 dark:bg-gray-800 dark:text-green-400"
                    role="alert"
                >
                    <span className="font-medium">Success: </span>
                    {success}
                </div>
            )}
            {error && (
                <div
                    className="p-4 my-4 text-sm text-red-800 rounded-lg bg-red-50 dark:bg-gray-800 dark:text-red-400"
                    role="alert"
                >
                    <span className="font-medium">Error: </span>
                    {error}
                </div>
            )}
        </div>
    )
}
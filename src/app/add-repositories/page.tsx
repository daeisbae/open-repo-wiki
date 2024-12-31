'use client'

import React, { useEffect, useState } from 'react'
import { insertRepository } from '@/app/add-repositories/insert-repo'
import Loading from '@/app/add-repositories/loading'

export default function AddRepository() {
    const [owner, setOwner] = useState('')
    const [repo, setRepo] = useState('')
    const [submit, setSubmit] = useState(false)

    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    useEffect(() => {
        if (!submit) return
        setSuccess(null)
        setError(null)
        const handleInsert = async () => {
            try {
                setIsLoading(true)
                const result = await insertRepository(owner, repo)

                if (!result.success) {
                    result.error
                        ? setError(result.error)
                        : setError('Failed to process repository')
                } else {
                    setSuccess(`Repository ${owner}/${repo} loaded into queue`)
                }
            } catch (err) {
                setError('Failed to process repository')
            }
        }
        handleInsert().then(() => {
            setIsLoading(false)
            setSubmit(false)
            setOwner('')
            setRepo('')
        })
    }, [owner, repo, submit])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
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
                    onClick={() => setSubmit(true)}
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

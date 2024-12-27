'use client'

import { MDXRemote } from 'next-mdx-remote'
import { serialize } from 'next-mdx-remote/serialize'
import { useState, useEffect } from 'react'
import React from 'react'
import { Skeleton } from '@/components/ui/skeleton'

interface MarkdownContentProps {
    content: string
}

export function MarkdownContent({ content }: MarkdownContentProps) {
    const [serializedContent, setSerializedContent] = useState<any>(null)

    useEffect(() => {
        const serializeMarkdown = async () => {
            const serialized = await serialize(content)
            setSerializedContent(serialized)
        }
        serializeMarkdown()
    }, [content])

    if (!serializedContent) {
        return <Skeleton className="h-[200px] w-full" />
    }

    return (
        <div className="prose dark:prose-invert max-w-none">
            <MDXRemote {...serializedContent} />
        </div>
    )
}

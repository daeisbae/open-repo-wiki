'use client'
import React, { Suspense } from 'react'
import Loading from '@/app/get/repositories/loading'
import ListAvailableWiki from '@/app/get/repositories/ListAvailableWiki'

export default function Page() {
    return (
        <div>
            <h1 className="text-3xl font-bold p-4 text-center" >Available Wiki Pages</h1>
                <ListAvailableWiki />
        </div>
    )
}

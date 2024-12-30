import React, { Suspense } from 'react'
import Loading from '@/app/repositories/loading'
import ListAvailableWiki from '@/app/repositories/ListAvailableWiki'

export default async function ListOfAvailableWikiPages() {
    return (
        <div>
            <h1>Available Wiki Pages</h1>
            <Suspense fallback={<Loading />}>
                <ListAvailableWiki />
            </Suspense>
        </div>
    )
}

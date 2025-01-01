import React, { Suspense } from 'react'
import Loading from '@/app/get/repositories/loading'
import ListAvailableWiki from '@/app/get/repositories/ListAvailableWiki'

export default async function ListOfAvailableWikiPages() {
    return (
        <div>
            <h1 className="text-3xl font-bold p-4" >Available Wiki Pages</h1>
            <Suspense fallback={<Loading />}>
                <ListAvailableWiki />
            </Suspense>
        </div>
    )
}

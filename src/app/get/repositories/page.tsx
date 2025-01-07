import React, { Suspense } from 'react'
import Loading from '@/app/get/repositories/loading'
import RepositoryList from '@/app/get/repositories/RepositoryList'

export default function Page() {
    return (
        <div>
            <h1 className="text-3xl font-bold p-4 text-center" >Available Wiki Pages</h1>
            <Suspense fallback={<Loading />}>
                <RepositoryList />
            </Suspense>
        </div>
    )
}

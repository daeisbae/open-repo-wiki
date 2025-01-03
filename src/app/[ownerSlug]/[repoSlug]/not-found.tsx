import Link from 'next/link'
import { JSX } from 'react'
import React from 'react'


export default async function NotFound(): Promise<JSX.Element> {

    return (
        <div className="flex flex-col items-center justify-center w-full h-full">
            <h1 className='text-lg md:text-3xl mb-6 text-center'>The repository is not created yet</h1>
            <div className="bg-black hover:bg-slate-900 text-white py-4 px-6 rounded-md">
                <Link href={{
                    pathname: '/add/repositories',
                }} >Create this repository</Link>
            </div>
        </div>
    )
}

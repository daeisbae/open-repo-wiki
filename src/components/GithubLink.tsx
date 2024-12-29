import Image from 'next/image'
import Github from '@/assets/github.png'
import React from 'react'

export default function GithubLink() {
    return (
        <a
            href="https://github.com/daeisbae/open-repo-wiki"
            className="fixed bottom-6 right-6"
            target="_blank"
        >
            <Image src={Github} alt="Github Logo" width={32} height={32} />
        </a>
    )
}

import * as React from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import github from '@/assets/github.png'

import {
    NavigationMenu,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
    navigationMenuTriggerStyle,
} from '@/components/ui/navigation-menu'
import Image from 'next/image'

export default function Navbar() {
    return (
        <div className="border-b">
            <div className="flex h-16 items-center px-4 justify-between max-w-7xl mx-auto">
                <Link href="/" className="flex items-center space-x-2">
                    <span className="text-xl font-bold">OpenRepoWiki</span>
                </Link>

                <NavigationMenu className="hidden md:flex">
                    <NavigationMenuList>
                        <NavigationMenuItem>
                            <Link href="/get/repositories" legacyBehavior passHref>
                                <NavigationMenuLink
                                    className={cn(
                                        navigationMenuTriggerStyle(),
                                        'w-28'
                                    )}
                                >
                                    Repo List
                                </NavigationMenuLink>
                            </Link>
                        </NavigationMenuItem>
                        <NavigationMenuItem>
                            <Link href="/add/repositories" legacyBehavior passHref>
                                <NavigationMenuLink
                                    className={cn(
                                        navigationMenuTriggerStyle(),
                                        'w-28'
                                    )}
                                >
                                    Add Repo
                                </NavigationMenuLink>
                            </Link>
                        </NavigationMenuItem>
                    </NavigationMenuList>
                </NavigationMenu>

                <a
                    href="https://github.com/daeisbae/open-repo-wiki"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors px-3 py-2 rounded-md hover:bg-gray-100"
                >
                    <Image src={github.src} width={16} height={16} alt="Link to the project github" />
                    <span className="text-sm hidden sm:inline">GitHub</span>
                </a>
            </div>
        </div>
    )
}

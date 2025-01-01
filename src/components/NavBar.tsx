import * as React from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

import {
    NavigationMenu,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
    navigationMenuTriggerStyle,
} from '@/components/ui/navigation-menu'

export default function Navbar() {
    return (
        <div className="border-b justify-between">
            <div className="flex h-16 items-center px-4">
                <Link href="/" className="mr-6 flex items-center space-x-2">
                    <span className="text-xl font-bold">OpenRepoWiki</span>
                </Link>
                <NavigationMenu>
                    <NavigationMenuList className="hidden md:flex">
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
            </div>
        </div>
    )
}

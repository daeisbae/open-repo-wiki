"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { cn } from "@/lib/utils";
import github from "@/assets/github.png";

import {
	NavigationMenu,
	NavigationMenuItem,
	NavigationMenuLink,
	NavigationMenuList,
	navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import {
	Sheet,
	SheetContent,
	SheetTitle,
	SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

export default function Navbar() {
	const [isVisible, setIsVisible] = useState(true);
	const [lastScrollY, setLastScrollY] = useState(0);

	const controlNavbar = () => {
		if (typeof window !== "undefined") {
			if (window.scrollY > lastScrollY) {
				// Scrolling down
				setIsVisible(false);
			} else {
				// Scrolling up
				setIsVisible(true);
			}
			setLastScrollY(window.scrollY);
		}
	};

	useEffect(() => {
		if (typeof window !== "undefined") {
			window.addEventListener("scroll", controlNavbar);

			return () => {
				window.removeEventListener("scroll", controlNavbar);
			};
		}
	}, [lastScrollY]);

	return (
		<div
			className={`fixed w-full top-0 left-0 border-b bg-white transition-transform duration-300 z-50 ${
				isVisible ? "transform translate-y-0" : "transform -translate-y-full"
			}`}
		>
			<div className="flex h-16 items-center px-4 justify-between max-w-7xl mx-auto">
				<Link href="/" className="flex items-center space-x-2">
					<span className="text-xl font-bold">OpenRepoWiki</span>
				</Link>

				<NavigationMenu className="hidden md:flex">
					<NavigationMenuList>
						<NavigationMenuItem>
							<Link href="/get/repositories" legacyBehavior passHref>
								<NavigationMenuLink
									className={cn(navigationMenuTriggerStyle(), "w-28")}
								>
									Repo List
								</NavigationMenuLink>
							</Link>
						</NavigationMenuItem>
						<NavigationMenuItem>
							<Link href="/add/repositories" legacyBehavior passHref>
								<NavigationMenuLink
									className={cn(navigationMenuTriggerStyle(), "w-28")}
								>
									Add Repo
								</NavigationMenuLink>
							</Link>
						</NavigationMenuItem>
					</NavigationMenuList>
				</NavigationMenu>

				<div className="flex items-center space-x-4">
					<a
						href="https://github.com/daeisbae/open-repo-wiki"
						target="_blank"
						rel="noopener noreferrer"
						className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors px-3 py-2 rounded-md hover:bg-gray-100"
					>
						<Image
							src={github.src}
							width={16}
							height={16}
							alt="Link to the project github"
						/>
						<span className="text-sm hidden sm:inline">GitHub</span>
					</a>

					<Sheet>
						<SheetTrigger asChild>
							<Button variant="outline" size="icon" className="md:hidden">
								<Menu className="h-6 w-6" />
								<span className="sr-only">Toggle menu</span>
							</Button>
						</SheetTrigger>
						<SheetContent
							side="right"
							className="w-[300px] sm:w-[400px] transform transition-transform duration-300 ease-in-out"
						>
							<SheetTitle>Menu</SheetTitle>
							<nav className="flex flex-col space-y-4 mt-4">
								<Link
									href="/get/repositories"
									className="text-lg font-medium hover:text-primary transition-colors"
								>
									Repo List
								</Link>
								<Link
									href="/add/repositories"
									className="text-lg font-medium hover:text-primary transition-colors"
								>
									Add Repo
								</Link>
							</nav>
						</SheetContent>
					</Sheet>
				</div>
			</div>
		</div>
	);
}

import GithubLink from '@/components/GithubLink'
import './globals.css'
import Navbar from '@/components/NavBar'

export const metadata = {
    title: 'OpenRepoWiki',
    description: 'A Wikipedia of Github Repositories of how it is made.',
    icons: {
        icon: '/favicon.ico',
    }
}

interface RootLayoutProps {
    children: React.ReactNode
}

export default function RootLayout({ children } : RootLayoutProps) {
    return (
        <html lang="en">
            <body className="bg-white">
                <Navbar />
                <main className="min-h-[calc(100vh-4rem)] flex items-center justify-center max-w-7xl mx-auto p-6">{children}</main>
                <GithubLink />
            </body>
        </html>
    )
}

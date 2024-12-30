import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card'
import { GitFork, Star } from 'lucide-react'

export default function RepositorySkeleton() {
    return (
        <Card className="w-[400px]">
            <CardHeader>
                <CardTitle className="h-6 w-3/4 bg-gray-200 rounded animate-pulse" />
                <CardDescription className="h-4 w-full bg-gray-200 rounded animate-pulse mt-2" />
            </CardHeader>
            <CardContent>
                <div className="flex items-center gap-4 mb-4">
                    <div className="flex items-center">
                        <Star className="w-4 h-4 mr-1 text-gray-300" />
                        <div className="h-4 w-8 bg-gray-200 rounded animate-pulse" />
                    </div>
                    <div className="flex items-center">
                        <GitFork className="w-4 h-4 mr-1 text-gray-300" />
                        <div className="h-4 w-8 bg-gray-200 rounded animate-pulse" />
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

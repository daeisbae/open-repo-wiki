'use client'

import * as React from 'react'
import { Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { redirect } from 'next/navigation'

export default function GitHubSearch() {
  const [searchValue, setSearchValue] = React.useState('')
  const [error, setError] = React.useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (searchValue.startsWith('https://github.com/')) {
      const parts = searchValue.replace('https://github.com/', '').split('/')
      if (parts.length >= 2) {
        return
      }
    }

    const parts = searchValue.split('/')
    if (parts.length === 2) {
      redirect(`/${parts[0]}/${parts[1]}`)
    }

    setError('Please enter a valid GitHub URL or owner/repo format (e.g., "owner/repo")')
  }

  return (
    <div className="flex flex-col justify-center items-center w-full max-w-xl mx-auto">
      <h1 className='flex items-center justify-center w-full max-w-xl py-4 text-lg sm:text-2xl md:text-3xl'>Github Repository to Wikipedia</h1>
      <Card className="w-full max-w-xl mx-auto">
        <CardContent className="pt-6 px-4 md:px-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Enter GitHub URL or owner/repo (e.g., daeisbae/open-repo-wiki)"
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  className="pl-9 py-6 text-[9px] sm:text-sm text-center"
                />
              </div>
            </div>
            <Button type="submit" className="w-full">
              Search Repository
            </Button>
          </form>
        </CardContent>
      </Card>
      <div className="h-8 mt-2"> {/* Fixed height container for error message */}
        {error && <p className="text-sm text-destructive text-red-500">{error}</p>}
      </div>
    </div>
  )
}

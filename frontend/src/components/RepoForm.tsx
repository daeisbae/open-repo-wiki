import { useState, type FormEvent } from 'react';

interface RepoFormProps {
  onSubmit: (owner: string, repo: string) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}

export function RepoForm({ onSubmit, isLoading = false, error }: RepoFormProps) {
  const [input, setInput] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    // Parse owner/repo format or GitHub URL
    // Supports:
    // - owner/repo
    // - https://github.com/owner/repo
    // - https://github.com/owner/repo/blob/main/...
    const regex = /^(?:https?:\/\/(?:www\.)?github\.com\/)?([^\/]+)\/([^\/\s]+)(?:\/.*)?$/;
    const match = trimmed.match(regex);

    if (match) {
      const [, owner, repo] = match;
      await onSubmit(owner, repo);
    }
  };

  const isValid = /^(?:https?:\/\/(?:www\.)?github\.com\/)?([^\/]+)\/([^\/\s]+)(?:\/.*)?$/.test(input.trim());

  return (
    <div className="bg-white min-h-screen flex flex-col">
      <div className="flex-1 flex flex-col justify-center items-center">
        <div className="w-full max-w-2xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold tracking-tight text-black sm:text-5xl mb-4">
              Open Repo Wiki
            </h1>
            <p className="text-xl text-gray-500">
              Generate documentation for any GitHub repository instantly.
            </p>
          </div>

          <div className="w-full relative">
            <form onSubmit={handleSubmit} className="relative">
              <div className="relative flex items-center">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="w-full rounded-full border-gray-300 py-4 pl-6 pr-16 text-lg border outline-none focus:border-black focus:ring-0"
                  placeholder="Enter GitHub repository (e.g., owner/repo)"
                  style={{ boxShadow: '0 0 15px rgba(0,0,0,0.1)' }}
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={!isValid || isLoading}
                  className={`absolute right-2 w-10 h-10 flex items-center justify-center rounded-full transition-colors ${
                    isValid && !isLoading
                      ? 'bg-black hover:bg-gray-800 cursor-pointer text-white'
                      : 'bg-gray-300 cursor-not-allowed text-white'
                  }`}
                >
                  {isLoading ? (
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  )}
                </button>
              </div>
            </form>

            {error && (
              <div className="absolute left-0 right-0 mt-4 rounded-md bg-red-50 p-4 border border-red-100">
                <div className="flex justify-center">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">{error}</h3>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="pb-6 text-center text-xs text-gray-400">
        <p>Open Repo Wiki can make mistakes. Consider checking important information.</p>
        <p className="mt-2">
          Made with{' '}
          <svg className="inline h-3 w-3 text-black" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
          </svg>{' '}
          by{' '}
          <a href="https://github.com/daeisbae" className="text-black hover:underline">
            daeisbae
          </a>
        </p>
      </div>
    </div>
  );
}

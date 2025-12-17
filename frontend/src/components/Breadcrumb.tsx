interface BreadcrumbProps {
  owner: string;
  repo: string;
  commitSha?: string;
  currentPath?: string;
  onNavigate: (path: string) => void;
  onGoToRoot: () => void;
}

export function Breadcrumb({
  owner,
  repo,
  commitSha,
  currentPath,
  onNavigate,
  onGoToRoot,
}: BreadcrumbProps) {
  const pathParts = currentPath ? currentPath.split('/').filter(Boolean) : [];

  const handlePathClick = (index: number) => {
    const path = pathParts.slice(0, index + 1).join('/');
    onNavigate(path);
  };

  return (
    <nav
      className="flex px-4 sm:px-6 lg:px-8 py-4 border-b border-gray-200 bg-white"
      aria-label="Breadcrumb"
    >
      <ol role="list" className="flex items-center space-x-4 max-w-7xl mx-auto w-full">
        {/* Home */}
        <li>
          <div>
            <a
              href="/"
              className="text-gray-400 hover:text-gray-500"
            >
              <svg className="flex-shrink-0 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
              </svg>
              <span className="sr-only">Home</span>
            </a>
          </div>
        </li>

        {/* Owner */}
        <li>
          <div className="flex items-center">
            <svg
              className="flex-shrink-0 h-5 w-5 text-gray-300"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
            <a
              href={`https://github.com/${owner}`}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700"
            >
              {owner}
            </a>
          </div>
        </li>

        {/* Repo */}
        <li>
          <div className="flex items-center">
            <svg
              className="flex-shrink-0 h-5 w-5 text-gray-300"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
            <a
              href={`https://github.com/${owner}/${repo}`}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700"
            >
              {repo}
            </a>
          </div>
        </li>

        {/* Commit SHA */}
        {commitSha && (
          <li>
            <div className="flex items-center">
              <svg
                className="flex-shrink-0 h-5 w-5 text-gray-300"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              <button
                onClick={onGoToRoot}
                className="ml-4 text-xs font-mono text-gray-400 hover:text-gray-600"
              >
                {commitSha.slice(0, 7)}
              </button>
            </div>
          </li>
        )}

        {/* Path parts */}
        {pathParts.map((part, index) => (
          <li key={index}>
            <div className="flex items-center">
              <svg
                className="flex-shrink-0 h-5 w-5 text-gray-300"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              <button
                onClick={() => handlePathClick(index)}
                className="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700"
              >
                {part}
              </button>
            </div>
          </li>
        ))}
      </ol>
    </nav>
  );
}

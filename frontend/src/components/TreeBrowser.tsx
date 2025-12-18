import { useState, useEffect } from 'react';

export interface TreeNode {
  type: 'folder' | 'file';
  name: string;
  path: string;
  parentPath: string;
  hasSummary: boolean;
}

interface TreeBrowserProps {
  repoId: string;
  branch: string;
  onSelectNode: (node: TreeNode) => void;
  selectedPath?: string;
  fetchTree: (repoId: string, branch: string, path: string) => Promise<TreeNode[]>;
}

interface TreeNodeItemProps {
  node: TreeNode;
  repoId: string;
  branch: string;
  onSelectNode: (node: TreeNode) => void;
  selectedPath?: string;
  fetchTree: (repoId: string, branch: string, path: string) => Promise<TreeNode[]>;
  level: number;
}

function TreeNodeItem({
  node,
  repoId,
  branch,
  onSelectNode,
  selectedPath,
  fetchTree,
  level,
}: TreeNodeItemProps) {
  const [isOpen, setIsOpen] = useState(level < 2);
  const [children, setChildren] = useState<TreeNode[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);

  const isSelected = selectedPath === node.path;
  const isFolder = node.type === 'folder';

  const loadChildren = async () => {
    if (hasLoaded || !isFolder) return;
    setIsLoading(true);
    try {
      const nodes = await fetchTree(repoId, branch, node.path);
      setChildren(nodes);
      setHasLoaded(true);
    } catch (err) {
      console.error('Failed to load children:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && isFolder && !hasLoaded) {
      loadChildren();
    }
  }, [isOpen]);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (isFolder) {
      setIsOpen(!isOpen);
    }
    onSelectNode(node);
  };

  return (
    <li>
      {isFolder ? (
        <details open={isOpen}>
          <summary
            onClick={handleClick}
            className={`group flex items-center px-2 py-1 text-sm font-medium text-gray-600 rounded-md hover:text-gray-900 hover:bg-gray-50 cursor-pointer list-none select-none ${
              isSelected ? 'bg-gray-100' : ''
            }`}
          >
            <svg
              className="mr-2 h-4 w-4 text-gray-400 group-hover:text-gray-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
            </svg>
            {node.name}
            {isLoading && (
              <svg className="ml-2 h-3 w-3 animate-spin text-gray-400" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
          </summary>
          {isOpen && children.length > 0 && (
            <div className="ml-4 border-l border-gray-200 pl-2">
              <ul className="space-y-1">
                {children.map((child) => (
                  <TreeNodeItem
                    key={child.path}
                    node={child}
                    repoId={repoId}
                    branch={branch}
                    onSelectNode={onSelectNode}
                    selectedPath={selectedPath}
                    fetchTree={fetchTree}
                    level={level + 1}
                  />
                ))}
              </ul>
            </div>
          )}
        </details>
      ) : (
        <a
          href="#"
          onClick={handleClick}
          className={`group flex items-center px-2 py-1 text-sm font-medium text-gray-600 rounded-md hover:text-gray-900 hover:bg-gray-50 ${
            isSelected ? 'bg-gray-100' : ''
          }`}
        >
          <svg
            className="mr-2 h-4 w-4 text-gray-400 group-hover:text-gray-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
              clipRule="evenodd"
            />
          </svg>
          {node.name}
          {!node.hasSummary && (
            <span className="ml-2 text-xs text-gray-400" title="No summary available">
              •
            </span>
          )}
        </a>
      )}
    </li>
  );
}

export function TreeBrowser({
  repoId,
  branch,
  onSelectNode,
  selectedPath,
  fetchTree,
}: TreeBrowserProps) {
  const [rootNodes, setRootNodes] = useState<TreeNode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalFiles, setTotalFiles] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const loadRoot = async () => {
      setIsLoading(true);
      try {
        const nodes = await fetchTree(repoId, branch, '');
        setRootNodes(nodes);
        // Count files for display
        const fileCount = nodes.filter((n) => n.type === 'file').length;
        setTotalFiles(fileCount);
      } catch (err) {
        console.error('Failed to load tree:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadRoot();
  }, [repoId, branch, fetchTree]);

  // Close mobile menu when a node is selected
  const handleSelectNode = (node: TreeNode) => {
    onSelectNode(node);
    setIsMobileMenuOpen(false);
  };

  return (
    <>
      {/* Mobile hamburger button */}
      <div className="lg:hidden flex items-center justify-between py-3 px-1 border-b border-gray-200">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          aria-expanded={isMobileMenuOpen}
          aria-controls="mobile-tree-menu"
        >
          {/* Hamburger icon */}
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {isMobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
          <span>Files</span>
          <span className="text-xs text-gray-500">
            {isLoading ? '...' : `(${totalFiles})`}
          </span>
        </button>
      </div>

      {/* Mobile collapsible menu */}
      <aside
        id="mobile-tree-menu"
        className={`lg:hidden overflow-y-auto transition-all duration-200 ease-in-out ${
          isMobileMenuOpen ? 'max-h-96 py-3 border-b border-gray-200' : 'max-h-0 overflow-hidden'
        }`}
      >
        <nav className="space-y-1 px-1" aria-label="Mobile Sidebar">
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <svg className="h-5 w-5 animate-spin text-gray-400" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          ) : (
            <ul className="space-y-1">
              {rootNodes.map((node) => (
                <TreeNodeItem
                  key={node.path}
                  node={node}
                  repoId={repoId}
                  branch={branch}
                  onSelectNode={handleSelectNode}
                  selectedPath={selectedPath}
                  fetchTree={fetchTree}
                  level={0}
                />
              ))}
            </ul>
          )}
        </nav>
      </aside>

      {/* Desktop sidebar - always visible on lg+ */}
      <aside className="hidden lg:block lg:col-span-3 h-full overflow-y-auto py-6 border-r border-gray-200">
        <nav className="space-y-1" aria-label="Sidebar">
          <div className="pb-4 mb-4 border-b border-gray-200">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Files
            </h3>
            <p className="mt-2 text-xs text-gray-500 leading-snug">
              {isLoading ? 'Loading...' : `Showing ${totalFiles} items.`}
            </p>
          </div>
          <div className="space-y-1">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <svg className="h-5 w-5 animate-spin text-gray-400" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
            ) : (
              <ul className="space-y-1">
                {rootNodes.map((node) => (
                  <TreeNodeItem
                    key={node.path}
                    node={node}
                    repoId={repoId}
                    branch={branch}
                    onSelectNode={onSelectNode}
                    selectedPath={selectedPath}
                    fetchTree={fetchTree}
                    level={0}
                  />
                ))}
              </ul>
            )}
          </div>
        </nav>
      </aside>
    </>
  );
}

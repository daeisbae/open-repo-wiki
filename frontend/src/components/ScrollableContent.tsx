import { useEffect, useState, useRef, useCallback } from 'react';
import { marked } from 'marked';
import mermaid from 'mermaid';
import type { TreeNode } from './TreeBrowser';
import type { PageContent } from './PageViewer';

interface FolderSection {
  path: string;
  displayName: string;
  depth: number;
  summary: string | null;
  isLoading: boolean;
  isLoaded: boolean;
  hasError: boolean;
}

interface ScrollableContentProps {
  repoId: string;
  branch: string;
  folders: TreeNode[];
  fetchPage: (repoId: string, branch: string, path: string) => Promise<PageContent>;
  onFolderClick?: (path: string) => void;
}

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'system-ui, -apple-system, sans-serif',
});

export function ScrollableContent({
  repoId,
  branch,
  folders,
  fetchPage,
  onFolderClick,
}: ScrollableContentProps) {
  const [sections, setSections] = useState<FolderSection[]>([]);
  const [rootSummary, setRootSummary] = useState<string | null>(null);
  const [isLoadingRoot, setIsLoadingRoot] = useState(true);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sectionRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Initialize sections from folders
  useEffect(() => {
    const collapsedFolders = collapseSingleChildFolders(folders);
    setSections(
      collapsedFolders.map((folder) => ({
        path: folder.path,
        displayName: folder.displayName,
        depth: folder.depth,
        summary: null,
        isLoading: false,
        isLoaded: false,
        hasError: false,
      }))
    );
  }, [folders]);

  // Helper to compose content from structured PageContent
  const composeContent = (page: PageContent): string => {
    if (page.legacy) {
      return page.summary;
    }
    let content = '';
    if (page.usage) content += `**${page.usage}**\n\n`;
    if (page.summary) content += page.summary;
    if (page.dependency_graph) {
      content += `\n\n## Dependency Graph\n\n\`\`\`mermaid\n${page.dependency_graph}\n\`\`\``;
    }
    return content;
  };

  // Load root summary on mount
  useEffect(() => {
    const loadRootSummary = async () => {
      setIsLoadingRoot(true);
      try {
        const page = await fetchPage(repoId, branch, '');
        setRootSummary(page.available ? composeContent(page) : null);
      } catch (err) {
        console.error('Failed to load root summary:', err);
        setRootSummary(null);
      } finally {
        setIsLoadingRoot(false);
      }
    };
    loadRootSummary();
  }, [repoId, branch, fetchPage]);

  // Load section content
  const loadSection = useCallback(
    async (path: string) => {
      setSections((prev) =>
        prev.map((s) =>
          s.path === path ? { ...s, isLoading: true } : s
        )
      );

      try {
        const page = await fetchPage(repoId, branch, path);
        const composedSummary = page.available ? composeContent(page) : null;
        setSections((prev) =>
          prev.map((s) =>
            s.path === path
              ? { ...s, summary: composedSummary, isLoading: false, isLoaded: true }
              : s
          )
        );
      } catch (err) {
        console.error(`Failed to load section ${path}:`, err);
        setSections((prev) =>
          prev.map((s) =>
            s.path === path
              ? { ...s, isLoading: false, isLoaded: true, hasError: true }
              : s
          )
        );
      }
    },
    [repoId, branch, fetchPage]
  );

  // Setup intersection observer for lazy loading
  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const path = entry.target.getAttribute('data-path');
            if (path) {
              const section = sections.find((s) => s.path === path);
              if (section && !section.isLoaded && !section.isLoading) {
                loadSection(path);
              }
            }
          }
        });
      },
      {
        rootMargin: '200px', // Pre-load sections 200px before they enter viewport
        threshold: 0.1,
      }
    );

    // Observe all section refs
    sectionRefs.current.forEach((element) => {
      observerRef.current?.observe(element);
    });

    return () => {
      observerRef.current?.disconnect();
    };
  }, [sections, loadSection]);

  // Register section ref
  const setSectionRef = useCallback(
    (path: string) => (el: HTMLDivElement | null) => {
      if (el) {
        sectionRefs.current.set(path, el);
        observerRef.current?.observe(el);
      } else {
        const existing = sectionRefs.current.get(path);
        if (existing) {
          observerRef.current?.unobserve(existing);
          sectionRefs.current.delete(path);
        }
      }
    },
    []
  );

  return (
    <div className="scrollable-content">
      {/* Root Summary */}
      <section className="root-summary">
        {isLoadingRoot ? (
          <LoadingSpinner />
        ) : rootSummary ? (
          <MarkdownRenderer content={rootSummary} />
        ) : (
          <p className="text-gray-500">No repository summary available.</p>
        )}
      </section>

      {/* Folder Sections */}
      {sections.map((section) => (
        <section
          key={section.path}
          ref={setSectionRef(section.path)}
          data-path={section.path}
          className="folder-section"
          style={{ marginLeft: `${section.depth * 1}rem` }}
        >
          <h2
            className="folder-heading"
            onClick={() => onFolderClick?.(section.path)}
          >
            <FolderIcon />
            <span>{section.displayName}</span>
          </h2>

          <div className="folder-content">
            {section.isLoading ? (
              <LoadingSpinner small />
            ) : section.hasError ? (
              <p className="text-red-500 text-sm">Failed to load summary</p>
            ) : section.summary ? (
              <MarkdownRenderer content={section.summary} />
            ) : !section.isLoaded ? (
              <div className="h-24 bg-gray-50 animate-pulse rounded" />
            ) : (
              <p className="text-gray-400 text-sm italic">No summary</p>
            )}
          </div>
        </section>
      ))}

      <style>{`
        .scrollable-content {
          max-width: 900px;
          padding-bottom: 4rem;
        }

        .root-summary {
          margin-bottom: 2rem;
          padding-bottom: 2rem;
          border-bottom: 1px solid #e5e7eb;
        }

        .folder-section {
          margin-bottom: 1.5rem;
          padding: 1rem;
          background: #f9fafb;
          border-radius: 0.5rem;
          border: 1px solid #e5e7eb;
        }

        .folder-heading {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 1.25rem;
          font-weight: 600;
          color: #1f2937;
          margin-bottom: 0.75rem;
          cursor: pointer;
        }

        .folder-heading:hover {
          color: #2563eb;
        }

        .folder-content {
          padding-left: 1.5rem;
        }

        /* Notion-style content */
        .folder-content h1,
        .folder-content h2,
        .folder-content h3 {
          font-size: 1.1rem;
          font-weight: 600;
          margin-top: 1rem;
          margin-bottom: 0.5rem;
        }

        .folder-content p {
          line-height: 1.6;
          color: #374151;
          margin-bottom: 0.75rem;
        }

        .folder-content code {
          background-color: #e0f2fe;
          color: #075985;
          padding: 0.15em 0.3em;
          border-radius: 0.25rem;
          font-size: 0.85em;
        }

        .folder-content pre {
          background-color: #1e293b;
          border-radius: 0.5rem;
          padding: 0.75rem;
          overflow-x: auto;
          margin: 0.75rem 0;
        }

        .folder-content pre code {
          background-color: transparent;
          color: #e2e8f0;
          padding: 0;
        }

        .mermaid-diagram {
          background-color: #fff;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          padding: 1rem;
          margin: 1rem 0;
          overflow-x: auto;
        }
      `}</style>
    </div>
  );
}

// Helper components
function LoadingSpinner({ small = false }: { small?: boolean }) {
  const size = small ? 'h-5 w-5' : 'h-8 w-8';
  return (
    <div className={`flex items-center justify-center ${small ? 'py-2' : 'py-8'}`}>
      <svg className={`${size} animate-spin text-gray-400`} viewBox="0 0 24 24">
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
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
    </div>
  );
}

function FolderIcon() {
  return (
    <svg className="h-5 w-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
      <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
    </svg>
  );
}

function MarkdownRenderer({ content }: { content: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderContent = async () => {
      if (!ref.current || !content) return;

      const html = marked.parse(content) as string;
      ref.current.innerHTML = html;

      // Render mermaid diagrams
      const mermaidBlocks = ref.current.querySelectorAll('pre > code.language-mermaid');
      for (let i = 0; i < mermaidBlocks.length; i++) {
        const block = mermaidBlocks[i];
        const code = block.textContent || '';
        const pre = block.parentElement;

        if (pre) {
          try {
            const { svg } = await mermaid.render(`mermaid-${Date.now()}-${i}`, code);
            const container = document.createElement('div');
            container.className = 'mermaid-diagram';
            container.innerHTML = svg;
            pre.replaceWith(container);
          } catch (err) {
            console.error('Failed to render mermaid:', err);
          }
        }
      }
    };

    renderContent();
  }, [content]);

  return <div ref={ref} />;
}

// Collapse single-child folder chains (frontend version)
interface CollapsedFolder {
  path: string;
  displayName: string;
  depth: number;
}

function collapseSingleChildFolders(folders: TreeNode[]): CollapsedFolder[] {
  if (!folders.length) return [];

  // Build parent -> children mapping
  const folderPaths = new Set(folders.filter((f) => f.type === 'folder').map((f) => f.path));
  const childrenMap = new Map<string, string[]>();

  for (const path of folderPaths) {
    const parts = path.split('/');
    if (parts.length > 1) {
      const parent = parts.slice(0, -1).join('/');
      if (folderPaths.has(parent)) {
        const children = childrenMap.get(parent) || [];
        children.push(path);
        childrenMap.set(parent, children);
      }
    }
  }

  // Find root folders
  const rootFolders: string[] = [];
  for (const path of folderPaths) {
    const parts = path.split('/');
    if (parts.length === 1) {
      rootFolders.push(path);
    } else {
      const parent = parts.slice(0, -1).join('/');
      if (!folderPaths.has(parent)) {
        rootFolders.push(path);
      }
    }
  }

  const result: CollapsedFolder[] = [];
  const skipFolders = new Set<string>();

  function findCollapseChain(startPath: string): string[] {
    const chain = [startPath];
    let current = startPath;

    while (true) {
      const children = childrenMap.get(current) || [];
      if (children.length !== 1) break;
      current = children[0];
      chain.push(current);
    }

    return chain;
  }

  function processFolder(folderPath: string, depth: number) {
    if (skipFolders.has(folderPath)) return;

    const chain = findCollapseChain(folderPath);
    const leafPath = chain[chain.length - 1];

    // Mark intermediate folders to skip
    for (let i = 0; i < chain.length - 1; i++) {
      skipFolders.add(chain[i]);
    }

    result.push({
      path: leafPath,
      displayName: leafPath,
      depth,
    });

    // Process children of the leaf
    const children = childrenMap.get(leafPath) || [];
    for (const child of children.sort()) {
      processFolder(child, depth + 1);
    }
  }

  for (const root of rootFolders.sort()) {
    processFolder(root, 0);
  }

  return result;
}

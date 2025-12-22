import { useEffect, useState, useRef } from 'react';
import { marked } from 'marked';
import mermaid from 'mermaid';
import type { TreeNode } from './TreeBrowser';

export interface PageContent {
  usage: string;
  summary: string;
  dependency_graph: string;
  available: boolean;
  legacy: boolean;
}

interface PageViewerProps {
  repoId: string;
  branch: string;
  selectedNode: TreeNode | null;
  repoSummary?: string;
  fetchPage: (repoId: string, branch: string, path: string) => Promise<PageContent>;
  onExpandRequest?: (node: TreeNode) => void;
}

// Initialize mermaid with custom config
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'system-ui, -apple-system, sans-serif',
});

export function PageViewer({
  repoId,
  branch,
  selectedNode,
  repoSummary,
  fetchPage,
  onExpandRequest,
}: PageViewerProps) {
  const [content, setContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAvailable, setIsAvailable] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadContent = async () => {
      if (!selectedNode) {
        // Show repo summary if no node selected
        if (repoSummary) {
          setContent(repoSummary);
          setIsAvailable(true);
        }
        return;
      }

      setIsLoading(true);
      try {
        const page = await fetchPage(repoId, branch, selectedNode.path);
        
        // Compose content from structured fields
        if (page.legacy) {
          // Legacy format: summary contains full markdown
          setContent(page.summary);
        } else if (page.available) {
          // New format: compose from usage, summary, and dependency_graph
          let composedContent = '';
          if (page.usage) {
            composedContent += `**${page.usage}**\n\n`;
          }
          if (page.summary) {
            composedContent += page.summary;
          }
          if (page.dependency_graph) {
            composedContent += `\n\n## Dependency Graph\n\n\`\`\`mermaid\n${page.dependency_graph}\n\`\`\``;
          }
          setContent(composedContent);
        } else {
          setContent('');
        }
        setIsAvailable(page.available);
      } catch (err) {
        console.error('Failed to load page:', err);
        setContent('');
        setIsAvailable(false);
      } finally {
        setIsLoading(false);
      }
    };

    loadContent();
  }, [repoId, branch, selectedNode, repoSummary, fetchPage]);

  // Render markdown and mermaid diagrams when content changes
  useEffect(() => {
    const renderContent = async () => {
      if (!contentRef.current || !content) return;

      // Parse markdown to HTML
      const html = marked.parse(content) as string;
      contentRef.current.innerHTML = html;

      // Find all mermaid code blocks
      const mermaidBlocks = contentRef.current.querySelectorAll('pre > code.language-mermaid');
      const renderedDiagrams: HTMLElement[] = [];
      
      // Render all mermaid diagrams first
      for (let i = 0; i < mermaidBlocks.length; i++) {
        const block = mermaidBlocks[i];
        const code = block.textContent || '';
        const pre = block.parentElement;
        
        if (pre) {
          try {
            // Use timestamp + index for unique ID to avoid conflicts
            const { svg } = await mermaid.render(`mermaid-${Date.now()}-${i}`, code);
            const container = document.createElement('div');
            container.className = 'mermaid-diagram';
            container.innerHTML = svg;
            renderedDiagrams.push(container);
            // Remove the original pre block
            pre.remove();
          } catch (err) {
            // Silently ignore mermaid syntax errors - just hide the broken diagram
            console.warn('Skipping invalid mermaid diagram:', err);
            pre.remove(); // Remove the broken mermaid block entirely
          }
        }
      }
      
      // Move all diagrams to right after the first heading (title)
      if (renderedDiagrams.length > 0 && contentRef.current) {
        const firstHeading = contentRef.current.querySelector('h1, h2, h3');
        const firstParagraph = contentRef.current.querySelector('p');
        
        // Create a container for all diagrams
        const diagramsContainer = document.createElement('div');
        diagramsContainer.className = 'diagrams-section';
        
        // Add all diagrams to the container (no heading)
        renderedDiagrams.forEach(diagram => {
          diagramsContainer.appendChild(diagram);
        });

        
        // Insert after the first heading+paragraph (title section), before rest of content
        if (firstHeading && firstParagraph) {
          // Find the paragraph right after the heading
          let insertPoint = firstParagraph.nextSibling;
          if (insertPoint) {
            contentRef.current.insertBefore(diagramsContainer, insertPoint);
          } else {
            contentRef.current.appendChild(diagramsContainer);
          }
        } else if (firstHeading) {
          // Just insert after the heading
          if (firstHeading.nextSibling) {
            contentRef.current.insertBefore(diagramsContainer, firstHeading.nextSibling);
          } else {
            contentRef.current.appendChild(diagramsContainer);
          }
        } else {
          // No headings, just prepend
          contentRef.current.insertBefore(diagramsContainer, contentRef.current.firstChild);
        }
        
        // Remove any "Dependency Graph" headings that are now orphaned (diagrams moved away)
        const allHeadings = contentRef.current.querySelectorAll('h1, h2, h3, h4');
        allHeadings.forEach(heading => {
          const text = heading.textContent?.toLowerCase().trim() || '';
          if (text.includes('dependency graph') || text.includes('dependency diagram')) {
            heading.remove();
          }
        });
      }

    };

    renderContent();
  }, [content]);


  const handleExpandClick = () => {
    if (selectedNode && onExpandRequest) {
      onExpandRequest(selectedNode);
    }
  };

  return (
    <main className="lg:col-span-9 h-full overflow-y-auto py-6">
      <div className="notion-content">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <svg className="h-8 w-8 animate-spin text-gray-400" viewBox="0 0 24 24">
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
        ) : !isAvailable && selectedNode?.type === 'file' ? (
          // Folder-only mode: show expand option for files
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 text-yellow-800 rounded">
            <p className="mb-3">
              File-level summary is not available. This repository was processed in folder-only mode.
            </p>
            {onExpandRequest && (
              <button
                onClick={handleExpandClick}
                className="inline-flex items-center px-3 py-2 border border-yellow-300 text-sm font-medium rounded-md text-yellow-800 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
              >
                <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Request on-demand summary
              </button>
            )}
          </div>
        ) : content ? (
          <div ref={contentRef} className="markdown-content" />
        ) : (
          <p className="text-gray-500 text-sm italic">
            {selectedNode ? 'No summary available.' : 'Select a file or folder to view its summary.'}
          </p>
        )}
      </div>

      <style>{`
        /* Notion-style content container */
        .notion-content {
          max-width: 900px;
          text-align: left;
        }

        /* Notion-style headings - large, bold, left-aligned */
        .notion-content h1 {
          font-size: 2.25rem;
          font-weight: 700;
          color: #1a1a1a;
          margin-top: 2rem;
          margin-bottom: 0.5rem;
          line-height: 1.2;
          text-align: left;
        }

        .notion-content h2 {
          font-size: 1.75rem;
          font-weight: 600;
          color: #1a1a1a;
          margin-top: 1.75rem;
          margin-bottom: 0.5rem;
          line-height: 1.3;
          text-align: left;
        }

        .notion-content h3 {
          font-size: 1.375rem;
          font-weight: 600;
          color: #1a1a1a;
          margin-top: 1.5rem;
          margin-bottom: 0.5rem;
          line-height: 1.4;
          text-align: left;
        }

        /* Paragraph styling */
        .notion-content p {
          font-size: 1rem;
          line-height: 1.75;
          color: #374151;
          margin-bottom: 1rem;
          text-align: left;
        }

        /* Code styling */
        .notion-content code {
          background-color: #e0f2fe;
          color: #075985;
          padding: 0.2em 0.4em;
          border-radius: 0.25rem;
          font-weight: 500;
          font-size: 0.875em;
        }

        .notion-content code::before,
        .notion-content code::after {
          content: '' !important;
        }

        /* Code block styling */
        .notion-content pre {
          background-color: #1e293b;
          border-radius: 0.5rem;
          padding: 1rem;
          overflow-x: auto;
          margin: 1rem 0;
        }

        .notion-content pre code {
          background-color: transparent;
          color: #e2e8f0;
          padding: 0;
          font-size: 0.875rem;
        }

        /* Link styling */
        .notion-content a {
          color: #2563eb;
          text-decoration: underline;
          text-underline-offset: 2px;
        }

        .notion-content a:hover {
          color: #1d4ed8;
        }

        /* List styling */
        .notion-content ul,
        .notion-content ol {
          margin-left: 1.5rem;
          margin-bottom: 1rem;
          text-align: left;
        }

        .notion-content li {
          margin-bottom: 0.5rem;
          line-height: 1.6;
        }

        /* Mermaid diagram container */
        .mermaid-diagram {
          background-color: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          padding: 1.5rem;
          margin: 0.5rem 0;
          overflow-x: auto;
          text-align: left;
        }

        .mermaid-diagram svg {
          max-width: 100%;
          height: auto;
        }

        /* Diagram section with heading */
        .diagrams-section {
          margin: 1.5rem 0;
        }

        .diagram-heading {
          font-size: 1.5rem !important;
          font-weight: 600 !important;
          color: #1a1a1a !important;
          margin-top: 0 !important;
          margin-bottom: 0.75rem !important;
        }

        /* Blockquote styling */
        .notion-content blockquote {
          border-left: 3px solid #3b82f6;
          padding-left: 1rem;
          margin: 1rem 0;
          color: #4b5563;
          font-style: italic;
        }

        /* Table styling */
        .notion-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 1rem 0;
        }

        .notion-content th,
        .notion-content td {
          border: 1px solid #e5e7eb;
          padding: 0.75rem;
          text-align: left;
        }

        .notion-content th {
          background-color: #f9fafb;
          font-weight: 600;
        }
      `}</style>
    </main>
  );
}

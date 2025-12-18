/**
 * Main App component with routing.
 *
 * Routes:
 * - / (Home): RepoForm for submitting repositories
 * - /processing/:jobId: ProgressView for tracking job progress
 * - /:owner/:repo: TreeBrowser and PageViewer for browsing documentation
 *
 * Requirements: 8.1, 8.2, 8.3
 */

import { BrowserRouter, Routes, Route, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useState, useCallback } from 'react';
import { RepoForm } from './components/RepoForm';
import { ProgressView } from './components/ProgressView';
import { TreeBrowser, type TreeNode } from './components/TreeBrowser';
import { PageViewer } from './components/PageViewer';
import { Breadcrumb } from './components/Breadcrumb';
import { createJob, getJob, getTree, getPage } from './api/client';
import './App.css';



/**
 * Home page with repository submission form.
 * Requirements: 8.1
 */
function HomePage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (owner: string, repo: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await createJob(owner, repo);
      
      if (result.status === 'completed') {
        // Job already completed - go directly to result page
        navigate(`/${owner}/${repo}`);
      } else {
        // New or in-progress job - go to processing page
        navigate(`/processing/${result.jobId}?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job');
      setIsLoading(false);
    }
  };

  return <RepoForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />;
}

/**
 * Processing page showing job progress.
 * Requirements: 8.2
 */
function ProcessingPage() {
  const navigate = useNavigate();
  const { jobId } = useParams<{ jobId: string }>();
  const [searchParams] = useSearchParams();

  const owner = searchParams.get('owner') || '';
  const repo = searchParams.get('repo') || '';

  const handleComplete = useCallback((repoId: string, branch: string) => {
    navigate(`/${repoId}?branch=${encodeURIComponent(branch)}`);
  }, [navigate]);

  const handleError = useCallback((error: string) => {
    console.error('Job failed:', error);
    // Stay on page to show error state
  }, []);

  if (!jobId) {
    navigate('/');
    return null;
  }

  return (
    <ProgressView
      jobId={jobId}
      owner={owner}
      repo={repo}
      onComplete={handleComplete}
      onError={handleError}
      fetchJob={getJob}
    />
  );
}


/**
 * Repository browser page with tree navigation and page viewer.
 * Requirements: 8.3
 */
function RepoPage() {
  const navigate = useNavigate();
  const { owner, repo } = useParams<{ owner: string; repo: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const branch = searchParams.get('branch') || 'main';
  const currentPath = searchParams.get('path') || '';

  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [repoSummary] = useState<string | undefined>(undefined);

  const repoId = `${owner}/${repo}`;

  const handleSelectNode = useCallback((node: TreeNode) => {
    setSelectedNode(node);
    setSearchParams((prev) => {
      prev.set('path', node.path);
      return prev;
    });
  }, [setSearchParams]);

  const handleNavigate = useCallback((path: string) => {
    setSearchParams((prev) => {
      prev.set('path', path);
      return prev;
    });
    setSelectedNode(null);
  }, [setSearchParams]);

  const handleGoToRoot = useCallback(() => {
    setSearchParams((prev) => {
      prev.delete('path');
      return prev;
    });
    setSelectedNode(null);
  }, [setSearchParams]);

  const handleExpandRequest = useCallback((node: TreeNode) => {
    console.log('Expand request for:', node.path);
  }, []);

  if (!owner || !repo) {
    navigate('/');
    return null;
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Breadcrumb
        owner={owner}
        repo={repo}
        currentPath={currentPath}
        onNavigate={handleNavigate}
        onGoToRoot={handleGoToRoot}
      />
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:grid lg:grid-cols-12 lg:gap-8 h-full">
          <TreeBrowser
            repoId={repoId}
            branch={branch}
            onSelectNode={handleSelectNode}
            selectedPath={selectedNode?.path || currentPath}
            fetchTree={getTree}
          />
          <PageViewer
            repoId={repoId}
            branch={branch}
            selectedNode={selectedNode}
            repoSummary={repoSummary}
            fetchPage={getPage}
            onExpandRequest={handleExpandRequest}
          />
        </div>
      </div>
    </div>
  );
}



/**
 * Main App component with router configuration.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/processing/:jobId" element={<ProcessingPage />} />
        <Route path="/:owner/:repo" element={<RepoPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

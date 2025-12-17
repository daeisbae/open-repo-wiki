import { useEffect, useState, useRef } from 'react';

export type JobStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
export type JobStage = 'FETCH_DETAILS' | 'FETCH_TREE' | 'FILTER' | 'SUMMARIZE_FILES' | 'SUMMARIZE_FOLDERS' | 'FINALIZE';

export interface Job {
  jobId: string;
  repoOwner: string;
  repoName: string;
  branch: string;
  status: JobStatus;
  stage: JobStage;
  processed: number;
  total: number;
  message: string;
  startedAt: string;
  updatedAt: string;
  finishedAt?: string;
  error?: string;
}

interface ProgressViewProps {
  jobId: string;
  owner: string;
  repo: string;
  onComplete: (repoId: string, branch: string) => void;
  onError: (error: string) => void;
  fetchJob: (jobId: string) => Promise<Job>;
}

const STAGE_LABELS: Record<JobStage, string> = {
  FETCH_DETAILS: 'Fetching repository details...',
  FETCH_TREE: 'Fetching file tree...',
  FILTER: 'Filtering files...',
  SUMMARIZE_FILES: 'Summarizing files...',
  SUMMARIZE_FOLDERS: 'Summarizing folders...',
  FINALIZE: 'Finalizing...',
};

export function ProgressView({ jobId, owner, repo, onComplete, onError, fetchJob }: ProgressViewProps) {
  const [job, setJob] = useState<Job | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const startTimeRef = useRef<Date | null>(null);
  const pollIntervalRef = useRef<number | null>(null);
  const timerIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    const pollJob = async () => {
      try {
        const data = await fetchJob(jobId);
        setJob(data);

        if (data.startedAt && !startTimeRef.current) {
          startTimeRef.current = new Date(data.startedAt);
        }

        // Adjust polling interval based on job status
        const currentInterval = pollIntervalRef.current;
        let newInterval = 5000; // Default to 5 seconds
        if (data.status === 'RUNNING' || data.status === 'PENDING') {
          newInterval = 1000; // Poll every 1 second if running
        }

        if (currentInterval && newInterval !== currentInterval) {
          clearInterval(currentInterval);
          pollIntervalRef.current = window.setInterval(pollJob, newInterval);
        } else if (!currentInterval) {
          pollIntervalRef.current = window.setInterval(pollJob, newInterval);
        }

        if (data.status === 'SUCCEEDED') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          const repoId = `${data.repoOwner}/${data.repoName}`;
          onComplete(repoId, data.branch);
        } else if (data.status === 'FAILED') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          onError(data.error || 'Processing failed');
        }
      } catch (err) {
        console.error('Failed to fetch job status:', err);
      }
    };

    // Initial fetch
    pollJob();

    // Timer update every second
    timerIntervalRef.current = window.setInterval(() => {
      if (startTimeRef.current) {
        const now = new Date();
        const diff = Math.floor((now.getTime() - startTimeRef.current.getTime()) / 1000);
        setElapsedTime(diff);
      }
    }, 1000);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [jobId, fetchJob, onComplete, onError]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getProgressPercent = () => {
    if (!job || job.total === 0) return 0;
    return Math.round((job.processed / job.total) * 100);
  };

  const getStatusMessage = () => {
    if (!job) return 'Initializing...';
    if (job.message) return job.message;
    return STAGE_LABELS[job.stage] || 'Processing...';
  };

  const isFailed = job?.status === 'FAILED';

  return (
    <div className="bg-white">
      <div className="max-w-7xl mx-auto py-16 px-4 sm:py-24 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-black sm:text-4xl">
            Processing {owner}/{repo}
          </h1>
          <div className="mt-6 max-w-2xl mx-auto">
            <p className="text-lg text-gray-500">
              We are generating the wiki for this repository. This may take a few minutes.
            </p>

            <div className="mt-8 relative pt-1">
              <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-200">
                {job && job.total > 0 ? (
                  <div
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-black transition-all duration-300"
                    style={{ width: `${getProgressPercent()}%` }}
                  />
                ) : (
                  <div className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-black w-full animate-pulse" />
                )}
              </div>
              {job && job.total > 0 && (
                <p className="text-sm text-gray-600 font-medium">
                  {job.processed} / {job.total} ({getProgressPercent()}%)
                </p>
              )}
            </div>

            <p
              id="status-message"
              className={`mt-2 text-sm ${isFailed ? 'text-red-500' : 'text-gray-500'}`}
            >
              {isFailed ? `Error: ${job?.error || 'Unknown error'}` : getStatusMessage()}
            </p>

            {job?.stage && !isFailed && (
              <p className="mt-1 text-xs text-gray-400 uppercase tracking-wide">
                Stage: {job.stage.replace(/_/g, ' ')}
              </p>
            )}

            {elapsedTime > 0 && (
              <p className="mt-1 text-xs text-gray-400">
                Time elapsed: {formatTime(elapsedTime)}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

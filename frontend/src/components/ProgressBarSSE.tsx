/**
 * ProgressBarSSE Component
 *
 * Real-time progress bar using Server-Sent Events (SSE) streaming.
 */

import { useProgressStream } from '../hooks/useProgressStream';
import type { SSEProgressMessage } from '../types/abm';
import { isJobFinished } from '../types/abm';

interface ProgressBarSSEProps {
  jobId: string | null;
  enabled?: boolean;
  onComplete?: (message: SSEProgressMessage) => void;
  onError?: (error: Error) => void;
  className?: string;
  showDetails?: boolean;
}

export function ProgressBarSSE({
  jobId,
  enabled = true,
  onComplete,
  onError,
  className = '',
  showDetails = true
}: ProgressBarSSEProps) {
  const {
    progress,
    isStreaming,
    error,
    progressPct,
    currentMonth,
    totalMonths,
    status
  } = useProgressStream(jobId, {
    enabled,
    onComplete,
    onError
  });

  if (!jobId) {
    return null;
  }

  const isFinished = status ? isJobFinished(status) : false;
  const barColor = isFinished
    ? status === 'completed'
      ? 'bg-green-600'
      : 'bg-red-600'
    : 'bg-blue-600';

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {isStreaming && !isFinished && (
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
          <span className="text-sm font-medium text-gray-700">
            {isStreaming && !isFinished ? 'Streaming progress...' : isFinished ? 'Complete' : 'Waiting...'}
          </span>
        </div>

        <div className="flex items-center space-x-4">
          {showDetails && currentMonth !== null && totalMonths !== null && (
            <span className="text-sm text-gray-600">
              Month {currentMonth} / {totalMonths}
            </span>
          )}
          <span className="text-sm font-semibold text-gray-900">
            {progressPct.toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="relative w-full bg-gray-200 rounded-full h-4 overflow-hidden shadow-inner">
        <div
          className={`${barColor} h-full transition-all duration-500 ease-out rounded-full flex items-center justify-end pr-2`}
          style={{ width: `${Math.min(100, progressPct)}%` }}
        >
          {progressPct > 10 && (
            <span className="text-xs font-medium text-white">
              {progressPct.toFixed(0)}%
            </span>
          )}
        </div>

        {isStreaming && !isFinished && (
          <div className="absolute top-0 left-0 w-full h-full overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer" />
          </div>
        )}
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">
            <span className="font-medium">Error:</span> {error}
          </p>
        </div>
      )}

      {showDetails && progress && (
        <div className="text-xs text-gray-500 space-y-1">
          <div className="flex items-center justify-between">
            <span>Status: {status}</span>
            <span>Job ID: {jobId.slice(0, 12)}...</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProgressBarSSE;

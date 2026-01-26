/**
 * JobStatusDisplay Component
 *
 * Displays current status of an ABM simulation job with visual indicators.
 */

import type { JobStatus } from '../types/abm';
import { JobStatus as JobStatusEnum, isJobCompleted, isJobFailed, isJobRunning, isJobPending } from '../types/abm';

interface JobStatusDisplayProps {
  jobId: string;
  status: JobStatus;
  progressPct?: number;
  currentMonth?: number;
  totalMonths?: number;
  errorMessage?: string;
  createdAt?: string;
  completedAt?: string;
  className?: string;
}

const STATUS_COLORS: Record<JobStatus, string> = {
  [JobStatusEnum.PENDING]: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  [JobStatusEnum.RUNNING]: 'bg-blue-100 text-blue-800 border-blue-300',
  [JobStatusEnum.COMPLETED]: 'bg-green-100 text-green-800 border-green-300',
  [JobStatusEnum.FAILED]: 'bg-red-100 text-red-800 border-red-300',
  [JobStatusEnum.CANCELLED]: 'bg-gray-100 text-gray-800 border-gray-300'
};

const STATUS_ICONS: Record<JobStatus, string> = {
  [JobStatusEnum.PENDING]: '⏳',
  [JobStatusEnum.RUNNING]: '▶️',
  [JobStatusEnum.COMPLETED]: '✅',
  [JobStatusEnum.FAILED]: '❌',
  [JobStatusEnum.CANCELLED]: '🚫'
};

const STATUS_LABELS: Record<JobStatus, string> = {
  [JobStatusEnum.PENDING]: 'Pending',
  [JobStatusEnum.RUNNING]: 'Running',
  [JobStatusEnum.COMPLETED]: 'Completed',
  [JobStatusEnum.FAILED]: 'Failed',
  [JobStatusEnum.CANCELLED]: 'Cancelled'
};

export function JobStatusDisplay({
  jobId,
  status,
  progressPct = 0,
  currentMonth,
  totalMonths,
  errorMessage,
  createdAt,
  completedAt,
  className = ''
}: JobStatusDisplayProps) {
  const statusColor = STATUS_COLORS[status];
  const statusIcon = STATUS_ICONS[status];
  const statusLabel = STATUS_LABELS[status];

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <div className={`rounded-lg border-2 p-6 ${statusColor} ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-3xl">{statusIcon}</span>
          <div>
            <h3 className="text-lg font-semibold">{statusLabel}</h3>
            <p className="text-sm opacity-75">Job ID: {jobId.slice(0, 12)}...</p>
          </div>
        </div>

        {isJobRunning(status) && progressPct > 0 && (
          <div className="text-right">
            <div className="text-2xl font-bold">{progressPct.toFixed(1)}%</div>
            {currentMonth !== undefined && totalMonths !== undefined && (
              <div className="text-sm opacity-75">
                Month {currentMonth} / {totalMonths}
              </div>
            )}
          </div>
        )}
      </div>

      {isJobRunning(status) && progressPct > 0 && (
        <div className="mb-4">
          <div className="w-full bg-white bg-opacity-50 rounded-full h-3 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300 ease-out rounded-full"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}

      {isJobFailed(status) && errorMessage && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm font-medium text-red-900 mb-1">Error:</p>
          <p className="text-sm text-red-700">{errorMessage}</p>
        </div>
      )}

      <div className="mt-4 flex items-center justify-between text-sm opacity-75">
        {createdAt && (
          <div>
            <span className="font-medium">Created:</span> {formatDate(createdAt)}
          </div>
        )}
        {isJobCompleted(status) && completedAt && (
          <div>
            <span className="font-medium">Completed:</span> {formatDate(completedAt)}
          </div>
        )}
      </div>

      {isJobCompleted(status) && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800 font-medium">
            Simulation completed successfully. Results are ready to view.
          </p>
        </div>
      )}

      {isJobPending(status) && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800 font-medium">
            Simulation is queued and will start shortly...
          </p>
        </div>
      )}
    </div>
  );
}

export default JobStatusDisplay;

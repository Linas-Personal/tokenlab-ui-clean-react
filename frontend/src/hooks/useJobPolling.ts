/**
 * useJobPolling Hook
 *
 * Polls job status at regular intervals until completion.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { JobStatus, isJobFinished } from '../types/abm';
import type { JobStatusResponse } from '../types/abm';
import { getJobStatus } from '../lib/abm-api';

interface UseJobPollingOptions {
  enabled?: boolean;
  pollInterval?: number;
  onComplete?: (status: JobStatusResponse) => void;
  onError?: (error: Error) => void;
  onProgress?: (status: JobStatusResponse) => void;
}

interface UseJobPollingReturn {
  status: JobStatusResponse | null;
  isPolling: boolean;
  error: string | null;
  startPolling: () => void;
  stopPolling: () => void;
  refetch: () => Promise<void>;
}

export function useJobPolling(
  jobId: string | null,
  options: UseJobPollingOptions = {}
): UseJobPollingReturn {
  const {
    enabled = true,
    pollInterval = 1000,
    onComplete,
    onError,
    onProgress
  } = options;

  const [status, setStatus] = useState<JobStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<number | null>(null);
  const isMountedRef = useRef<boolean>(true);

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const poll = useCallback(async () => {
    if (!jobId) {
      stopPolling();
      return;
    }

    try {
      const statusResponse = await getJobStatus(jobId);

      if (!isMountedRef.current) {
        return;
      }

      setStatus(statusResponse);
      setError(null);

      if (onProgress) {
        onProgress(statusResponse);
      }

      if (isJobFinished(statusResponse.status)) {
        stopPolling();

        if (onComplete) {
          onComplete(statusResponse);
        }
      }
    } catch (err) {
      if (!isMountedRef.current) {
        return;
      }

      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch job status';
      setError(errorMessage);
      stopPolling();

      if (onError && err instanceof Error) {
        onError(err);
      }
    }
  }, [jobId, stopPolling, onComplete, onError, onProgress]);

  const startPolling = useCallback(() => {
    if (!jobId || isPolling) {
      return;
    }

    setIsPolling(true);
    setError(null);

    poll();

    intervalRef.current = window.setInterval(poll, pollInterval);
  }, [jobId, isPolling, poll, pollInterval]);

  const refetch = useCallback(async (): Promise<void> => {
    await poll();
  }, [poll]);

  useEffect(() => {
    isMountedRef.current = true;

    if (enabled && jobId && !isJobFinished(status?.status || JobStatus.PENDING)) {
      startPolling();
    }

    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [enabled, jobId, status?.status, startPolling, stopPolling]);

  return {
    status,
    isPolling,
    error,
    startPolling,
    stopPolling,
    refetch
  };
}

export default useJobPolling;

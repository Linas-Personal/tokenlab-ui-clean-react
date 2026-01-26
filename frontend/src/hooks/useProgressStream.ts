/**
 * useProgressStream Hook
 *
 * Streams real-time progress updates via Server-Sent Events (SSE).
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { SSEProgressMessage, JobStatus } from '../types/abm';
import { streamJobProgress } from '../lib/abm-api';

interface UseProgressStreamOptions {
  enabled?: boolean;
  onComplete?: (message: SSEProgressMessage) => void;
  onError?: (error: Error) => void;
  onProgress?: (message: SSEProgressMessage) => void;
}

interface UseProgressStreamReturn {
  progress: SSEProgressMessage | null;
  isStreaming: boolean;
  error: string | null;
  progressPct: number;
  currentMonth: number | null;
  totalMonths: number | null;
  status: JobStatus | null;
  startStream: () => void;
  stopStream: () => void;
}

export function useProgressStream(
  jobId: string | null,
  options: UseProgressStreamOptions = {}
): UseProgressStreamReturn {
  const {
    enabled = true,
    onComplete,
    onError,
    onProgress
  } = options;

  const [progress, setProgress] = useState<SSEProgressMessage | null>(null);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const isMountedRef = useRef<boolean>(true);

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const handleMessage = useCallback((message: SSEProgressMessage) => {
    if (!isMountedRef.current) {
      return;
    }

    setProgress(message);
    setError(null);

    if (onProgress) {
      onProgress(message);
    }

    if (message.type === 'done' || message.type === 'error') {
      stopStream();

      if (message.type === 'done' && onComplete) {
        onComplete(message);
      }

      if (message.type === 'error') {
        const errorMessage = message.error_message || 'Stream error';
        setError(errorMessage);

        if (onError) {
          onError(new Error(errorMessage));
        }
      }
    }
  }, [stopStream, onComplete, onError, onProgress]);

  const handleError = useCallback((_event: Event) => {
    if (!isMountedRef.current) {
      return;
    }

    const errorMessage = 'SSE connection error';
    setError(errorMessage);
    stopStream();

    if (onError) {
      onError(new Error(errorMessage));
    }
  }, [stopStream, onError]);

  const startStream = useCallback(() => {
    if (!jobId || isStreaming) {
      return;
    }

    stopStream();

    setIsStreaming(true);
    setError(null);

    const eventSource = streamJobProgress(jobId, handleMessage, handleError);
    eventSourceRef.current = eventSource;
  }, [jobId, isStreaming, stopStream, handleMessage, handleError]);

  useEffect(() => {
    isMountedRef.current = true;

    if (enabled && jobId) {
      startStream();
    }

    return () => {
      isMountedRef.current = false;
      stopStream();
    };
  }, [enabled, jobId, startStream, stopStream]);

  return {
    progress,
    isStreaming,
    error,
    progressPct: progress?.progress_pct || 0,
    currentMonth: progress?.current_month || null,
    totalMonths: progress?.total_months || null,
    status: progress?.status || null,
    startStream,
    stopStream
  };
}

export default useProgressStream;

/**
 * useABMSimulation Hook
 *
 * Main hook for running ABM simulations with job management.
 */

import { useState, useCallback } from 'react';
import { JobStatus } from '../types/abm';
import type {
  ABMSimulationRequest,
  ABMSimulationResults,
  JobSubmissionResponse
} from '../types/abm';
import { submitABMSimulation, getJobResults, cancelJob } from '../lib/abm-api';

interface UseABMSimulationState {
  isSubmitting: boolean;
  isRunning: boolean;
  isCompleted: boolean;
  isFailed: boolean;
  isCancelled: boolean;
  error: string | null;
  jobId: string | null;
  results: ABMSimulationResults | null;
  cached: boolean;
}

interface UseABMSimulationReturn extends UseABMSimulationState {
  submit: (config: ABMSimulationRequest) => Promise<JobSubmissionResponse>;
  fetchResults: () => Promise<void>;
  cancel: () => Promise<void>;
  reset: () => void;
  status: JobStatus | null;
}

export function useABMSimulation(): UseABMSimulationReturn {
  const [state, setState] = useState<UseABMSimulationState>({
    isSubmitting: false,
    isRunning: false,
    isCompleted: false,
    isFailed: false,
    isCancelled: false,
    error: null,
    jobId: null,
    results: null,
    cached: false
  });

  const submit = useCallback(async (config: ABMSimulationRequest): Promise<JobSubmissionResponse> => {
    setState(prev => ({
      ...prev,
      isSubmitting: true,
      error: null,
      results: null
    }));

    try {
      const response = await submitABMSimulation(config);

      setState(prev => ({
        ...prev,
        isSubmitting: false,
        isRunning: !response.cached,
        isCompleted: response.cached,
        jobId: response.job_id,
        cached: response.cached,
        error: null
      }));

      if (response.cached) {
        await fetchResults(response.job_id);
      }

      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to submit simulation';
      setState(prev => ({
        ...prev,
        isSubmitting: false,
        isFailed: true,
        error: errorMessage
      }));
      throw error;
    }
  }, []);

  const fetchResults = useCallback(async (jobIdOverride?: string): Promise<void> => {
    const jobId = jobIdOverride || state.jobId;

    if (!jobId) {
      throw new Error('No job ID available');
    }

    try {
      const results = await getJobResults(jobId);
      setState(prev => ({
        ...prev,
        results,
        isCompleted: true,
        isRunning: false,
        error: null
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch results';
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isFailed: true,
        isRunning: false
      }));
      throw error;
    }
  }, [state.jobId]);

  const cancel = useCallback(async (): Promise<void> => {
    if (!state.jobId) {
      throw new Error('No job ID to cancel');
    }

    try {
      await cancelJob(state.jobId);
      setState(prev => ({
        ...prev,
        isRunning: false,
        isCancelled: true,
        error: null
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to cancel job';
      setState(prev => ({
        ...prev,
        error: errorMessage
      }));
      throw error;
    }
  }, [state.jobId]);

  const reset = useCallback((): void => {
    setState({
      isSubmitting: false,
      isRunning: false,
      isCompleted: false,
      isFailed: false,
      isCancelled: false,
      error: null,
      jobId: null,
      results: null,
      cached: false
    });
  }, []);

  const getStatus = (): JobStatus | null => {
    if (state.isSubmitting) return null;
    if (state.isCancelled) return JobStatus.CANCELLED;
    if (state.isFailed) return JobStatus.FAILED;
    if (state.isCompleted) return JobStatus.COMPLETED;
    if (state.isRunning) return JobStatus.RUNNING;
    return null;
  };

  return {
    ...state,
    submit,
    fetchResults,
    cancel,
    reset,
    status: getStatus()
  };
}

export default useABMSimulation;

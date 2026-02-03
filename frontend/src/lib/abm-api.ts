import axios, { type AxiosError } from 'axios'
import type {
  ABMSimulationRequest,
  ABMSimulationResults,
  JobListResponse,
  JobStatusResponse,
  JobSubmissionResponse,
  MonteCarloResults,
  QueueStatsResponse,
  SSEProgressMessage,
  ABMValidationResponse
} from '@/types/abm'

const DEFAULT_TIMEOUT_MS = 60000
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: DEFAULT_TIMEOUT_MS,
  headers: { 'Content-Type': 'application/json' }
})

const toErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string | { message?: string } }>
    if (axiosError.response?.data?.detail) {
      if (typeof axiosError.response.data.detail === 'string') {
        return axiosError.response.data.detail
      }
      if (axiosError.response.data.detail?.message) {
        return axiosError.response.data.detail.message
      }
    }
    return axiosError.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unexpected error'
}

export const submitABMSimulation = async (
  config: ABMSimulationRequest
): Promise<JobSubmissionResponse> => {
  try {
    const response = await api.post<JobSubmissionResponse>('/api/v2/abm/simulate', config)
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const runABMSimulationSync = async (
  config: ABMSimulationRequest
): Promise<ABMSimulationResults> => {
  try {
    const response = await api.post<ABMSimulationResults>('/api/v2/abm/simulate-sync', config)
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const getJobStatus = async (jobId: string): Promise<JobStatusResponse> => {
  try {
    const response = await api.get<JobStatusResponse>(`/api/v2/abm/jobs/${jobId}/status`)
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const getJobResults = async (jobId: string): Promise<ABMSimulationResults> => {
  try {
    const response = await api.get<ABMSimulationResults>(`/api/v2/abm/jobs/${jobId}/results`)
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const cancelJob = async (
  jobId: string
): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await api.delete<{ message: string }>(`/api/v2/abm/jobs/${jobId}`)
    return { success: true, message: response.data.message }
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const listJobs = async (): Promise<JobListResponse> => {
  try {
    const response = await api.get<JobListResponse>('/api/v2/abm/jobs')
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const getQueueStats = async (): Promise<QueueStatsResponse> => {
  try {
    const response = await api.get<QueueStatsResponse>('/api/v2/abm/queue/stats')
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const streamJobProgress = (
  jobId: string,
  onMessage: (message: SSEProgressMessage) => void,
  onError: (event: Event) => void
): EventSource => {
  const streamUrl = `${BASE_URL}/api/v2/abm/jobs/${jobId}/stream`
  const eventSource = new EventSource(streamUrl)

  eventSource.onmessage = (event: MessageEvent) => {
    try {
      const parsed = JSON.parse(event.data) as SSEProgressMessage
      onMessage(parsed)
    } catch {
      onError(new Event('parse-error'))
    }
  }

  eventSource.onerror = onError

  return eventSource
}

export const waitForJobCompletion = async (
  jobId: string,
  pollIntervalMs = 1000,
  onProgress?: (status: JobStatusResponse) => void
): Promise<ABMSimulationResults> => {
  while (true) {
    const status = await getJobStatus(jobId)
    if (onProgress) {
      onProgress(status)
    }
    if (status.status === 'completed') {
      return getJobResults(jobId)
    }
    if (status.status === 'failed') {
      throw new Error(status.error || 'Job failed')
    }
    await new Promise(resolve => setTimeout(resolve, pollIntervalMs))
  }
}

export const submitMonteCarloSimulation = async (
  config: ABMSimulationRequest
): Promise<JobSubmissionResponse> => {
  try {
    const response = await api.post<JobSubmissionResponse>('/api/v2/abm/monte-carlo/simulate', config)
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const getMonteCarloResults = async (jobId: string): Promise<MonteCarloResults> => {
  try {
    const response = await api.get<MonteCarloResults>(`/api/v2/abm/monte-carlo/results/${jobId}`)
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

export const validateABMConfig = async (
  config: ABMSimulationRequest
): Promise<ABMValidationResponse> => {
  try {
    const response = await api.post<ABMValidationResponse>('/api/v2/abm/validate', { config })
    return response.data
  } catch (error) {
    throw new Error(toErrorMessage(error))
  }
}

const abmAPIClient = {
  submitABMSimulation,
  runABMSimulationSync,
  getJobStatus,
  getJobResults,
  cancelJob,
  listJobs,
  getQueueStats,
  streamJobProgress,
  waitForJobCompletion,
  submitMonteCarloSimulation,
  getMonteCarloResults,
  validateABMConfig
}

export default abmAPIClient

import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

const HEALTH_ENDPOINT = `${BACKEND_URL}/api/v1/health`
const STARTUP_TIMEOUT_MS = 30000
const POLL_INTERVAL_MS = 500

let backendProcess: ChildProcessWithoutNullStreams | null = null
let startedByTests = false
let startPromise: Promise<void> | null = null
let activeUsers = 0

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const isBackendHealthy = async (): Promise<boolean> => {
  try {
    const response = await fetch(HEALTH_ENDPOINT, { method: 'GET' })
    return response.ok
  } catch {
    return false
  }
}

const getBackendWorkingDir = (): string => {
  const currentFile = fileURLToPath(import.meta.url)
  const currentDir = path.dirname(currentFile)
  return path.resolve(currentDir, '../../../..', 'backend')
}

const startBackendProcess = (): void => {
  const backendDir = getBackendWorkingDir()
  backendProcess = spawn(
    'python',
    ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
    {
      cwd: backendDir,
      env: {
        ...process.env,
        PROMETHEUS_ENABLED: 'false',
        LOG_LEVEL: 'warning'
      }
    }
  )
  startedByTests = true
}

const waitForBackend = async (): Promise<void> => {
  const deadline = Date.now() + STARTUP_TIMEOUT_MS

  while (Date.now() < deadline) {
    if (await isBackendHealthy()) {
      return
    }
    await sleep(POLL_INTERVAL_MS)
  }

  throw new Error(`Backend did not become healthy within ${STARTUP_TIMEOUT_MS}ms`)
}

export const ensureBackend = async (): Promise<void> => {
  activeUsers += 1
  if (await isBackendHealthy()) {
    return
  }

  if (!startPromise) {
    startPromise = (async () => {
      startBackendProcess()
      await waitForBackend()
    })()
  }

  await startPromise
}

export const stopBackend = async (): Promise<void> => {
  activeUsers = Math.max(0, activeUsers - 1)
  if (activeUsers > 0 || !startedByTests || !backendProcess) {
    return
  }

  return new Promise(resolve => {
    backendProcess?.once('exit', () => resolve())
    backendProcess?.kill('SIGTERM')
    backendProcess = null
    startedByTests = false
    startPromise = null
  })
}

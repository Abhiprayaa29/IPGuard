import { useCallback, useEffect, useRef, useState } from 'react'
import { createAuthSession, pollAuthSessionStatus } from '../services/auth'
import type {
  AuthStatus,
  SessionCreateResponse,
  SessionStatusResponse,
  SessionType,
} from '../types/auth'

const DEFAULT_TTL_SECONDS = 60
const POLLING_INTERVAL_MS = 1500

export function useQrAuth(
  initialType: SessionType = 'AUTHENTICATION',
  autoStart: boolean = true,
) {
  const [sessionType, setSessionType] = useState<SessionType>(initialType)
  const [status, setStatus] = useState<AuthStatus>('INITIAL')
  const [session, setSession] = useState<SessionCreateResponse | null>(null)
  const [pollResult, setPollResult] = useState<SessionStatusResponse | null>(null)
  const [secondsRemaining, setSecondsRemaining] = useState<number>(DEFAULT_TTL_SECONDS)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // SEC-02 In-Memory Secret: Held only in ephemeral component memory
  // NEVER written to localStorage, sessionStorage, or query params
  const channelTokenRef = useRef<string | null>(null)
  const pollingTimerRef = useRef<number | null>(null)
  const countdownTimerRef = useRef<number | null>(null)
  const activeSessionTokenRef = useRef<string | null>(null)
  const requestIdRef = useRef<number>(0)

  const clearTimers = useCallback(() => {
    if (pollingTimerRef.current !== null) {
      window.clearInterval(pollingTimerRef.current)
      pollingTimerRef.current = null
    }
    if (countdownTimerRef.current !== null) {
      window.clearInterval(countdownTimerRef.current)
      countdownTimerRef.current = null
    }
  }, [])

  const stopPolling = useCallback(() => {
    if (pollingTimerRef.current !== null) {
      window.clearInterval(pollingTimerRef.current)
      pollingTimerRef.current = null
    }
  }, [])

  const startSession = useCallback(
    async (type: SessionType = sessionType) => {
      clearTimers()
      const reqId = ++requestIdRef.current
      setSessionType(type)
      setStatus('CREATING')
      setErrorMessage(null)
      setPollResult(null)
      setSession(null)
      channelTokenRef.current = null
      activeSessionTokenRef.current = null

      try {
        const origin = window.location.origin
        const newSession = await createAuthSession(type, origin)

        // Drop stale async response if another session was requested
        if (requestIdRef.current !== reqId) {
          return
        }

        // Store private channel token in ephemeral memory only
        channelTokenRef.current = newSession.browser_channel_token
        activeSessionTokenRef.current = newSession.session_token

        setSession(newSession)
        setStatus('READY')

        // Calculate actual seconds remaining based on expires_at
        const expiresAtMs = new Date(newSession.expires_at).getTime()
        const initialSeconds = Math.max(
          0,
          Math.floor((expiresAtMs - Date.now()) / 1000),
        )
        setSecondsRemaining(initialSeconds > 0 ? initialSeconds : DEFAULT_TTL_SECONDS)

        // Ensure timers from any previous tick are dead
        clearTimers()

        // Start countdown timer guarded by requestId
        countdownTimerRef.current = window.setInterval(() => {
          if (requestIdRef.current !== reqId) {
            if (countdownTimerRef.current !== null) {
              window.clearInterval(countdownTimerRef.current)
              countdownTimerRef.current = null
            }
            return
          }
          setSecondsRemaining((prev) => {
            if (prev <= 1) {
              clearTimers()
              setStatus('EXPIRED')
              return 0
            }
            return prev - 1
          })
        }, 1000)

        // Start polling interval guarded by requestId
        const pollInterval = newSession.poll_interval_ms || POLLING_INTERVAL_MS
        pollingTimerRef.current = window.setInterval(async () => {
          if (requestIdRef.current !== reqId) {
            if (pollingTimerRef.current !== null) {
              window.clearInterval(pollingTimerRef.current)
              pollingTimerRef.current = null
            }
            return
          }

          const currentToken = activeSessionTokenRef.current
          const currentSecret = channelTokenRef.current

          if (!currentToken || !currentSecret) {
            return
          }

          try {
            const res = await pollAuthSessionStatus(currentToken, currentSecret)
            if (requestIdRef.current !== reqId) {
              return
            }

            setPollResult(res)

            if (res.status === 'SCANNED') {
              setStatus('SCANNED')
            } else if (res.status === 'APPROVED') {
              clearTimers()
              setStatus('APPROVED')
            } else if (res.status === 'REJECTED') {
              clearTimers()
              setStatus('REJECTED')
            } else if (res.status === 'EXPIRED') {
              clearTimers()
              setStatus('EXPIRED')
            }
          } catch (err: unknown) {
            if (requestIdRef.current !== reqId) {
              return
            }
            // If polling error is 403 or fatal session error, halt polling
            const msg = err instanceof Error ? err.message : 'Polling failure'
            if (msg.includes('403') || msg.includes('404')) {
              clearTimers()
              setStatus('ERROR')
              setErrorMessage(msg)
            }
          }
        }, pollInterval)
      } catch (err: unknown) {
        if (requestIdRef.current !== reqId) {
          return
        }
        clearTimers()
        setStatus('ERROR')
        setErrorMessage(
          err instanceof Error
            ? err.message
            : 'Failed to create authentication session.',
        )
      }
    },
    [clearTimers, sessionType],
  )

  const cancelSession = useCallback(() => {
    requestIdRef.current++
    clearTimers()
    channelTokenRef.current = null
    activeSessionTokenRef.current = null
    setStatus('INITIAL')
    setSession(null)
    setPollResult(null)
    setErrorMessage(null)
  }, [clearTimers])

  // Mount-only autoStart effect
  const hasAutoStartedRef = useRef(false)
  useEffect(() => {
    if (autoStart && !hasAutoStartedRef.current) {
      hasAutoStartedRef.current = true
      startSession(initialType)
    }
    return () => {
      clearTimers()
    }
  }, [autoStart, initialType, startSession, clearTimers])

  return {
    status,
    sessionType,
    session,
    pollResult,
    secondsRemaining,
    errorMessage,
    startSession,
    cancelSession,
    stopPolling,
  }
}

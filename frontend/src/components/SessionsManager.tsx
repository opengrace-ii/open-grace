import { useState, useEffect } from 'react'
import { APIClient } from '../api/client'
import './SessionsManager.css'

interface Session {
  session_id: string
  user_id: string
  username: string
  is_admin: boolean
  device_name: string
  ip_address: string
  created_at: string
  last_activity: string
}

export function SessionsManager() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [terminating, setTerminating] = useState<string | null>(null)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      setLoading(true)
      const data = await APIClient.getSessions()
      setSessions(data.sessions || [])
    } catch (err) {
      setError('Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }

  const handleTerminateAll = async () => {
    if (!confirm('Are you sure you want to terminate ALL your sessions on all devices? You will be logged out everywhere.')) {
      return
    }

    try {
      setTerminating('all')
      await APIClient.terminateAllSessions()
      alert('All sessions terminated. You will be redirected to login.')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    } catch (err) {
      setError('Failed to terminate sessions')
      setTerminating(null)
    }
  }

  const handleTerminateSession = async (sessionId: string) => {
    if (!confirm('Terminate this session?')) {
      return
    }

    try {
      setTerminating(sessionId)
      await APIClient.terminateSession(sessionId)
      await loadSessions()
    } catch (err) {
      setError('Failed to terminate session')
    } finally {
      setTerminating(null)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  if (loading) {
    return <div className="sessions-loading">Loading sessions...</div>
  }

  return (
    <div className="sessions-manager">
      <div className="sessions-header">
        <h2>Active Sessions</h2>
        <button 
          className="terminate-all-btn"
          onClick={handleTerminateAll}
          disabled={terminating === 'all'}
        >
          {terminating === 'all' ? 'Terminating...' : 'Logout All Devices'}
        </button>
      </div>

      {error && <div className="sessions-error">{error}</div>}

      <div className="sessions-list">
        {sessions.length === 0 ? (
          <div className="no-sessions">No active sessions found</div>
        ) : (
          sessions.map(session => (
            <div key={session.session_id} className="session-card">
              <div className="session-info">
                <div className="session-user">
                  <span className="username">{session.username}</span>
                  {session.is_admin && <span className="admin-badge">Admin</span>}
                </div>
                <div className="session-device">{session.device_name}</div>
                <div className="session-meta">
                  <span>IP: {session.ip_address || 'Unknown'}</span>
                  <span>Created: {formatDate(session.created_at)}</span>
                  <span>Last active: {formatDate(session.last_activity)}</span>
                </div>
              </div>
              <button
                className="terminate-btn"
                onClick={() => handleTerminateSession(session.session_id)}
                disabled={terminating === session.session_id}
              >
                {terminating === session.session_id ? '...' : 'Terminate'}
              </button>
            </div>
          ))
        )}
      </div>

      <div className="sessions-summary">
        <p>Total active sessions: <strong>{sessions.length}</strong></p>
        <p className="sessions-hint">
          Click "Logout All Devices" to terminate all your sessions across all devices.
        </p>
      </div>
    </div>
  )
}
import { useState, useEffect, useRef } from 'react'
import { Terminal, Trash2, RefreshCw } from 'lucide-react'
import { API_BASE_URL } from '../api/client'
import './ActivityLog.css'

export function ActivityLog() {
  const [logs, setLogs] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Fetch the full log file on mount and on refresh
  const fetchLogs = async () => {
    try {
      setError(null)
      const res = await fetch(`${API_BASE_URL}/observability/activity/history`)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
        setError(err.detail || `HTTP ${res.status}`)
        return
      }
      const data = await res.json()
      setLogs(data.lines || [])
    } catch (err: any) {
      setError('Failed to connect to the server.')
    }
  }

  useEffect(() => {
    fetchLogs()
    // Poll every 3 seconds 
    const interval = setInterval(fetchLogs, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs])

  const clearLogs = () => setLogs([])

  return (
    <div className="activity-log-container">
      <div className="log-header">
        <div className="header-title">
          <Terminal size={18} />
          <h3>System Activity Trace</h3>
        </div>
        <div className="header-actions">
          <button className="action-btn" onClick={fetchLogs} title="Refresh Now">
            <RefreshCw size={16} />
            Refresh
          </button>
          <button className="action-btn" onClick={clearLogs} title="Clear View">
            <Trash2 size={16} />
          </button>
        </div>
      </div>
      
      <div className="log-content" ref={scrollRef}>
        {error ? (
          <div className="empty-logs">
            <p style={{color: '#ef4444'}}>⚠ {error}</p>
            <p>The server may need to be restarted to enable logging endpoints.</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="empty-logs">
            <p>No activity yet. Interact with the app to generate trace entries.</p>
          </div>
        ) : (
          logs.map((log, i) => {
            // Format: "2026-03-12 14:05:33 | [INFO] | CLIENT | UI | ..."
            const parts = log.split(' | ')
            const time = parts[0] || ''
            const level = (parts[1] || '').replace(/[\[\]]/g, '').toLowerCase()
            const msg = parts.slice(2).join(' | ')
            return (
              <div key={i} className={`log-line ${level}`}>
                <span className="log-time">{time}</span>
                <span className="log-msg">{msg || log}</span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

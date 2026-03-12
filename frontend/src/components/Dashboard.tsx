import { useState, useEffect } from 'react'
import {
  Activity,
  Users,
  CheckCircle,
  Clock,
  AlertCircle,
  LogOut,
  Plus,
  Server,
  Shield,
  FileText,
  Activity as ActivityIcon
} from 'lucide-react'
import { APIClient } from '../api/client'
import { StatsCard } from './StatsCard'
import { TaskList } from './TaskList'
import { AgentList } from './AgentList'
import { CreateTaskModal } from './CreateTaskModal'
import { SessionsManager } from './SessionsManager'
import { ActivityLog } from './ActivityLog'
import { DiagnosticsPanel } from './DiagnosticsPanel'
import './Dashboard.css'

interface DashboardProps {
  onLogout: () => void
}

interface SystemStatus {
  instance_id: string
  initialized: boolean
  agents: {
    total: number
    active: number
    idle: number
  }
  tasks: {
    total: number
    pending: number
    running: number
    completed: number
    failed: number
  }
  queue_size: number
}

export function Dashboard({ onLogout }: DashboardProps) {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'sessions' | 'logs' | 'diagnostics'>('dashboard')

  useEffect(() => {
    // Sync tab with URL on mount
    const path = window.location.pathname.substring(1)
    if (['sessions', 'logs', 'diagnostics'].includes(path)) {
      setActiveTab(path as any)
    }
    
    loadData()
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [statusData, userData] = await Promise.all([
        APIClient.getSystemStatus(),
        APIClient.getCurrentUser()
      ])
      setStatus(statusData)
      setUser(userData)
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleTaskCreated = () => {
    setShowCreateModal(false)
    setRefreshTrigger(prev => prev + 1)
    loadData()
  }

  if (loading) {
    return (
      <div className="dashboard loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>Open Grace</h1>
          <span className="version">v0.4.0</span>
        </div>
        <div className="header-center">
          <nav className="tab-nav">
            <button 
              className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('dashboard')
                window.history.pushState(null, '', '/')
              }}
            >
              Dashboard
            </button>
            <button 
              className={`tab-btn ${activeTab === 'sessions' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('sessions')
                window.history.pushState(null, '', '/sessions')
                APIClient.logActivity('Switched to Sessions tab', 'Navigation')
              }}
            >
              <Shield size={16} />
              Sessions
            </button>
            <button 
              className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('logs')
                window.history.pushState(null, '', '/logs')
                APIClient.logActivity('Switched to Logs tab', 'Navigation')
              }}
            >
              <FileText size={16} />
              Logs
            </button>
            <button 
              className={`tab-btn ${activeTab === 'diagnostics' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('diagnostics')
                window.history.pushState(null, '', '/diagnostics')
                APIClient.logActivity('Switched to Diagnostics tab', 'Navigation')
              }}
            >
              <ActivityIcon size={16} />
              Diagnostics
            </button>
          </nav>
        </div>
        <div className="header-right">
          {user && (
            <div className="user-info">
              <span className="username">{user.username}</span>
              {user.is_admin && <span className="badge admin">Admin</span>}
            </div>
          )}
          <button className="logout-btn" onClick={onLogout}>
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        {activeTab === 'dashboard' ? (
          <>
            <div className="stats-grid">
              <StatsCard
                title="Total Tasks"
                value={status?.tasks.total || 0}
                icon={<CheckCircle size={24} />}
                color="blue"
              />
              <StatsCard
                title="Running"
                value={status?.tasks.running || 0}
                icon={<Activity size={24} />}
                color="green"
              />
              <StatsCard
                title="Pending"
                value={status?.tasks.pending || 0}
                icon={<Clock size={24} />}
                color="orange"
              />
              <StatsCard
                title="Failed"
                value={status?.tasks.failed || 0}
                icon={<AlertCircle size={24} />}
                color="red"
              />
              <StatsCard
                title="Active Agents"
                value={status?.agents.active || 0}
                icon={<Users size={24} />}
                color="purple"
              />
              <StatsCard
                title="Queue Size"
                value={status?.queue_size || 0}
                icon={<Server size={24} />}
                color="cyan"
              />
            </div>

            <div className="dashboard-content">
              <div className="content-section">
                <div className="section-header">
                  <h2>Tasks</h2>
                  <button 
                    className="create-btn"
                    onClick={() => setShowCreateModal(true)}
                  >
                    <Plus size={18} />
                    New Task
                  </button>
                </div>
                <TaskList refreshTrigger={refreshTrigger} />
              </div>

              <div className="content-section">
                <div className="section-header">
                  <h2>Agents</h2>
                </div>
                <AgentList />
              </div>
            </div>
          </>
        ) : activeTab === 'sessions' ? (
          <SessionsManager />
        ) : activeTab === 'logs' ? (
          <ActivityLog />
        ) : (
          <DiagnosticsPanel />
        )}
      </main>

      {showCreateModal && (
        <CreateTaskModal
          onClose={() => setShowCreateModal(false)}
          onCreated={handleTaskCreated}
        />
      )}
    </div>
  )
}
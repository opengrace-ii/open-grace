import { useState, useEffect } from 'react'
import { User, Cpu, Activity, Power } from 'lucide-react'
import { APIClient } from '../api/client'
import './AgentList.css'

interface Agent {
  id: string
  name: string
  agent_type: string
  status: 'idle' | 'busy' | 'offline'
  capabilities: string[]
  task_count: number
}

export function AgentList() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAgents()
    const interval = setInterval(loadAgents, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadAgents = async () => {
    try {
      const data = await APIClient.getAgents()
      setAgents(data)
    } catch (err) {
      console.error('Failed to load agents:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'busy':
        return <Activity size={16} className="status-busy" />
      case 'idle':
        return <Power size={16} className="status-idle" />
      default:
        return <Power size={16} className="status-offline" />
    }
  }

  if (loading) {
    return <div className="agent-list loading">Loading agents...</div>
  }

  return (
    <div className="agent-list">
      {agents.length === 0 ? (
        <div className="no-agents">No agents available</div>
      ) : (
        <div className="agent-grid">
          {agents.map((agent) => (
            <div key={agent.id} className={`agent-card ${agent.status}`}>
              <div className="agent-header">
                <div className="agent-icon">
                  <User size={24} />
                </div>
                <div className="agent-status">
                  {getStatusIcon(agent.status)}
                </div>
              </div>
              
              <div className="agent-info">
                <h4>{agent.name}</h4>
                <span className="agent-type">{agent.agent_type}</span>
              </div>

              <div className="agent-stats">
                <div className="stat">
                  <Cpu size={14} />
                  <span>{agent.task_count} tasks</span>
                </div>
              </div>

              <div className="agent-capabilities">
                {agent.capabilities.slice(0, 3).map((cap) => (
                  <span key={cap} className="capability-tag">
                    {cap}
                  </span>
                ))}
                {agent.capabilities.length > 3 && (
                  <span className="capability-more">
                    +{agent.capabilities.length - 3}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
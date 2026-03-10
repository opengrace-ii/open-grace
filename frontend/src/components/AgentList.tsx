import { useState, useEffect } from 'react'
import { Brain, Code, Terminal, Search, Activity, Power } from 'lucide-react'
import { APIClient } from '../api/client'
import './AgentList.css'

interface AgentStatus {
  id: string
  name: string
  type: string
  description: string
  icon: React.ReactNode
  status: 'idle' | 'busy' | 'offline'
  capabilities: string[]
}

const BUILT_IN_AGENTS: AgentStatus[] = [
  {
    id: 'planner',
    name: 'Planner',
    type: 'planner',
    description: 'Breaks down complex tasks and coordinates other agents',
    icon: <Brain size={20} />,
    status: 'idle',
    capabilities: ['Task decomposition', 'Agent coordination', 'Planning']
  },
  {
    id: 'coder',
    name: 'Coder',
    type: 'coder',
    description: 'Writes, reviews, and refactors code in multiple languages',
    icon: <Code size={20} />,
    status: 'idle',
    capabilities: ['Python', 'JavaScript', 'Code review', 'Debugging']
  },
  {
    id: 'sysadmin',
    name: 'SysAdmin',
    type: 'sysadmin',
    description: 'Manages Docker, shell commands, and system operations',
    icon: <Terminal size={20} />,
    status: 'idle',
    capabilities: ['Docker', 'Shell', 'System monitoring', 'Deployment']
  },
  {
    id: 'researcher',
    name: 'Researcher',
    type: 'researcher',
    description: 'Conducts research and builds knowledge graphs',
    icon: <Search size={20} />,
    status: 'idle',
    capabilities: ['Web search', 'Knowledge graphs', 'Data analysis']
  }
]

export function AgentList() {
  const [agents, setAgents] = useState<AgentStatus[]>(BUILT_IN_AGENTS)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      const data = await APIClient.getAgents()
      if (data && data.length > 0) {
        setAgents(BUILT_IN_AGENTS)
      }
    } catch (err) {
      console.log('Using static agent list')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'busy':
        return <Activity size={14} className="status-busy" />
      case 'idle':
        return <Power size={14} className="status-idle" />
      default:
        return <Power size={14} className="status-offline" />
    }
  }

  if (loading) {
    return <div className="agent-list loading">Loading agents...</div>
  }

  return (
    <div className="agent-list">
      <div className="agent-grid">
        {agents.map((agent) => (
          <div key={agent.id} className={`agent-card ${agent.status}`}>
            <div className="agent-header">
              <div className="agent-icon">
                {agent.icon}
              </div>
              <div className="agent-status">
                {getStatusIcon(agent.status)}
              </div>
            </div>
            
            <div className="agent-info">
              <h4>{agent.name}</h4>
              <span className="agent-type">{agent.type}</span>
            </div>

            <div className="agent-description">
              {agent.description}
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
    </div>
  )
}
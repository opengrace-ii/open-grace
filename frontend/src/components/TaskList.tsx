import { useState, useEffect } from 'react'
import { Play, CheckCircle, XCircle, Clock, RotateCcw, X } from 'lucide-react'
import { APIClient } from '../api/client'
import './TaskList.css'

interface Task {
  id: string
  description: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  agent_type: string | null
  created_at: string
  result: any
  model?: string
  tokens_used?: number
}

interface TaskListProps {
  refreshTrigger?: number
}

export function TaskList({ refreshTrigger }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  useEffect(() => {
    loadTasks()
    const interval = setInterval(loadTasks, 3000)
    return () => clearInterval(interval)
  }, [refreshTrigger])

  const loadTasks = async () => {
    try {
      const data = await APIClient.getTasks(filter || undefined)
      setTasks(data)
    } catch (err) {
      console.error('Failed to load tasks:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatModelName = (modelId: string) => {
    // Extract model name from ID like 'ollama-llama3' -> 'Llama 3'
    if (modelId.includes('-')) {
      const parts = modelId.split('-')
      const name = parts.slice(1).join(' ')
      return name.charAt(0).toUpperCase() + name.slice(1)
    }
    return modelId
  }

  const handleCancel = async (taskId: string) => {
    try {
      await APIClient.cancelTask(taskId)
      loadTasks()
    } catch (err) {
      console.error('Failed to cancel task:', err)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <RotateCcw className="spin" size={16} />
      case 'completed':
        return <CheckCircle size={16} />
      case 'failed':
        return <XCircle size={16} />
      case 'cancelled':
        return <XCircle size={16} />
      default:
        return <Clock size={16} />
    }
  }

  const getStatusClass = (status: string) => {
    return `status-badge ${status}`
  }

  if (loading) {
    return <div className="task-list loading">Loading tasks...</div>
  }

  return (
    <div className="task-list">
      <div className="filter-bar">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="task-table">
        <div className="task-header">
          <span>Task</span>
          <span>Agent</span>
          <span>Model</span>
          <span>Tokens</span>
          <span>Status</span>
          <span>Created</span>
          <span>Actions</span>
        </div>

        {tasks.length === 0 ? (
          <div className="no-tasks">No tasks found</div>
        ) : (
          tasks.map((task) => (
            <div key={task.id} className="task-row" onClick={() => setSelectedTask(task)} style={{cursor: 'pointer'}}>
              <div className="task-description" title={task.description}>
                {task.description}
              </div>
              <div className="task-agent">
                {task.agent_type || 'Auto'}
              </div>
              <div className="task-model">
                {task.model ? formatModelName(task.model) : <span className="no-data">-</span>}
              </div>
              <div className="task-tokens">
                {task.tokens_used ? task.tokens_used.toLocaleString() : <span className="no-data">-</span>}
              </div>
              <div className={getStatusClass(task.status)}>
                {getStatusIcon(task.status)}
                {task.status}
              </div>
              <div className="task-created">
                {new Date(task.created_at).toLocaleString()}
              </div>
              <div className="task-actions">
                {(task.status === 'pending' || task.status === 'running') && (
                  <button 
                    className="cancel-btn"
                    onClick={() => handleCancel(task.id)}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="task-modal-overlay" onClick={() => setSelectedTask(null)}>
          <div className="task-modal" onClick={(e) => e.stopPropagation()}>
            <div className="task-modal-header">
              <h3>Task Details</h3>
              <button className="close-btn" onClick={() => setSelectedTask(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="task-modal-content">
              <div className="task-detail-row">
                <span className="label">Description:</span>
                <span className="value">{selectedTask.description}</span>
              </div>
              <div className="task-detail-row">
                <span className="label">Status:</span>
                <span className={`status-badge ${selectedTask.status}`}>
                  {getStatusIcon(selectedTask.status)}
                  {selectedTask.status}
                </span>
              </div>
              <div className="task-detail-row">
                <span className="label">Agent:</span>
                <span className="value">{selectedTask.agent_type || 'Auto'}</span>
              </div>
              <div className="task-detail-row">
                <span className="label">Created:</span>
                <span className="value">{new Date(selectedTask.created_at).toLocaleString()}</span>
              </div>
              {selectedTask.model && (
                <div className="task-detail-row">
                  <span className="label">Model:</span>
                  <span className="value model-badge-display">
                    {selectedTask.model}
                  </span>
                </div>
              )}
              {selectedTask.tokens_used && (
                <div className="task-detail-row">
                  <span className="label">Tokens:</span>
                  <span className="value">{selectedTask.tokens_used.toLocaleString()}</span>
                </div>
              )}
              {selectedTask.result && (
                <div className="task-result">
                  <span className="label">Result:</span>
                  <div className="result-content">
                    {(() => {
                      // Extract content from result object
                      let content = ''
                      if (typeof selectedTask.result === 'string') {
                        content = selectedTask.result
                      } else if (selectedTask.result?.content) {
                        content = selectedTask.result.content
                      } else if (selectedTask.result?.result?.content) {
                        content = selectedTask.result.result.content
                      } else {
                        content = JSON.stringify(selectedTask.result, null, 2)
                      }
                      
                      // Convert escape sequences to actual formatting
                      content = content
                        .replace(/\\n/g, '\n')
                        .replace(/\\t/g, '  ')
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
                        .replace(/`([^`]+)`/g, '<code>$1</code>')
                      
                      // Split by newlines and render
                      return content.split('\n').map((line, i) => {
                        // Handle bullet points
                        if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
                          return <div key={i} className="bullet-point">• {line.trim().substring(2)}</div>
                        }
                        // Handle numbered lists
                        if (/^\d+\./.test(line.trim())) {
                          return <div key={i} className="numbered-point">{line.trim()}</div>
                        }
                        // Handle headers
                        if (line.trim().startsWith('# ')) {
                          return <h1 key={i} className="result-header">{line.trim().substring(2)}</h1>
                        }
                        if (line.trim().startsWith('## ')) {
                          return <h2 key={i} className="result-header">{line.trim().substring(3)}</h2>
                        }
                        // Regular line
                        return <div key={i} className="result-line" dangerouslySetInnerHTML={{ __html: line || '&nbsp;' }} />
                      })
                    })()}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
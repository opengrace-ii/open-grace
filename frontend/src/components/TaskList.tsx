import React, { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Clock, RotateCcw, X } from 'lucide-react'
import { APIClient } from '../api/client'
import './TaskList.css'

interface Task {
  id: string
  id_numeric: number
  description: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'branching' | 'evaluating' | 'rolling_back'
  agent_type: string | null
  created_at: string
  result: any
  model?: string
  tokens_used?: number
  latency_ms?: number
  provider?: string
  error?: string
  user?: string
  client_ip?: string
}

interface TaskListProps {
  refreshTrigger?: number
}

export function TaskList({ refreshTrigger }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  // --- Column Resizing Logic ---
  const [columnWidths, setColumnWidths] = useState({
    task: 300,
    agent: 100,
    model: 140,
    latency: 100,
    status: 130,
    created: 180,
    user: 140
  })

  useEffect(() => {
    loadTasks()
    const interval = setInterval(loadTasks, 3000)
    return () => clearInterval(interval)
  }, [refreshTrigger, filter])

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
      await APIClient.logActivity(`Cancelled Task: ${taskId}`, 'Task')
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

  const handleResizeStart = (e: React.MouseEvent, column: keyof typeof columnWidths) => {
    e.preventDefault()
    e.stopPropagation()
    const startX = e.pageX
    const startWidth = columnWidths[column]

    const onMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(50, startWidth + (e.pageX - startX))
      setColumnWidths(prev => ({ ...prev, [column]: newWidth }))
    }

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
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

      <div className="task-table-wrapper">
        <table className="task-table-native">
          <thead>
            <tr className="task-header">
              <th style={{ width: columnWidths.task, minWidth: columnWidths.task }}>
                <div className="th-content">
                  <span>Task</span>
                  <div className="resize-handle" onMouseDown={(e) => handleResizeStart(e, 'task')} />
                </div>
              </th>
              <th style={{ width: columnWidths.agent, minWidth: columnWidths.agent }}>
                <div className="th-content">
                  <span>Agent</span>
                  <div className="resize-handle" onMouseDown={(e) => handleResizeStart(e, 'agent')} />
                </div>
              </th>
              <th style={{ width: columnWidths.model, minWidth: columnWidths.model }}>
                <div className="th-content">
                  <span>Model</span>
                  <div className="resize-handle" onMouseDown={(e) => handleResizeStart(e, 'model')} />
                </div>
              </th>
              <th style={{ width: columnWidths.latency, minWidth: columnWidths.latency }}>
                <div className="th-content">
                  <span>Latency</span>
                  <div className="resize-handle" onMouseDown={(e) => handleResizeStart(e, 'latency')} />
                </div>
              </th>
              <th style={{ width: columnWidths.status, minWidth: columnWidths.status }}>
                <div className="th-content">
                  <span>Status</span>
                  <div className="resize-handle" onMouseDown={(e) => handleResizeStart(e, 'status')} />
                </div>
              </th>
              <th style={{ width: columnWidths.created, minWidth: columnWidths.created }}>
                <div className="th-content">
                  <span>Created</span>
                  <div className="resize-handle" onMouseDown={(e) => handleResizeStart(e, 'created')} />
                </div>
              </th>
              <th style={{ width: columnWidths.user, minWidth: columnWidths.user }}>
                <div className="th-content">
                  <span>User Info</span>
                  <div className="resize-handle" onMouseDown={(e) => handleResizeStart(e, 'user')} />
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {tasks.length === 0 ? (
              <tr>
                <td colSpan={7} className="no-tasks" style={{textAlign: 'center', padding: '40px', color: '#64748b'}}>No tasks found</td>
              </tr>
            ) : (
              tasks.map((task) => (
                <tr 
                  key={task.id} 
                  className="task-row" 
                  onClick={() => {
                    setSelectedTask(task)
                    APIClient.logActivity(`Viewed Task Details: ${task.id}`, 'UI')
                  }} 
                  style={{cursor: 'pointer'}}
                >
                  <td className="task-description" style={{ width: columnWidths.task, maxWidth: columnWidths.task }} title={task.description}>
                    {task.description}
                  </td>
                  <td className="task-agent" style={{ width: columnWidths.agent, maxWidth: columnWidths.agent }}>
                    {task.agent_type || 'Auto'}
                  </td>
                  <td className="task-model" style={{ width: columnWidths.model, maxWidth: columnWidths.model }} title={task.provider ? `Provider: ${task.provider}` : ''}>
                    {task.model ? formatModelName(task.model) : <span className="no-data">-</span>}
                  </td>
                  <td className="task-latency" style={{ width: columnWidths.latency, maxWidth: columnWidths.latency }}>
                    {task.latency_ms ? `${(task.latency_ms / 1000).toFixed(2)}s` : <span className="no-data">-</span>}
                  </td>
                  <td style={{ width: columnWidths.status, maxWidth: columnWidths.status, verticalAlign: 'middle' }}>
                    <div className={getStatusClass(task.status)}>
                      {getStatusIcon(task.status)}
                      <span className="status-text">{task.status}</span>
                    </div>
                  </td>
                  <td className="task-created" style={{ width: columnWidths.created, maxWidth: columnWidths.created }}>
                    {new Date(task.created_at).toLocaleString()}
                  </td>
                  <td className="task-user" style={{ width: columnWidths.user, maxWidth: columnWidths.user }}>
                    <div style={{fontWeight: 600}}>{task.user || 'Auto'}</div>
                    <div style={{fontSize: '11px', color: '#8b949e'}}>{task.client_ip || 'Unknown'}</div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="task-modal-overlay" onClick={() => setSelectedTask(null)}>
          <div className="task-modal" onClick={(e) => e.stopPropagation()}>
            <div className="task-modal-header">
              <div className="modal-title-group">
                <h3>Task Details</h3>
                <span className="task-number-badge">Task #{selectedTask.id_numeric}</span>
              </div>
              <div className="modal-actions">
                <button 
                  className="share-btn"
                  onClick={() => {
                    let content = '';
                    if (typeof selectedTask.result === 'string') {
                      content = selectedTask.result;
                    } else if (selectedTask.result?.content) {
                      content = selectedTask.result.content;
                    } else if (selectedTask.result?.result?.content) {
                      content = selectedTask.result.result.content;
                    } else {
                      content = JSON.stringify(selectedTask.result, null, 2);
                    }
                    
                    const shareText = `*Question:* ${selectedTask.description}\n\n*Response:* ${content}\n\n---\n*Open Grace TaskForge AI* | Task #${selectedTask.id_numeric}\n_Intelligence Unleashed_`;
                    
                    if (navigator.clipboard && window.isSecureContext) {
                        navigator.clipboard.writeText(shareText).then(() => {
                            alert("Response copied to clipboard!");
                        }).catch(() => {
                            // Fallback to manual copy if clipboard API fails
                            const textArea = document.createElement("textarea");
                            textArea.value = shareText;
                            document.body.appendChild(textArea);
                            textArea.select();
                            try {
                                document.execCommand('copy');
                                alert("Response copied to clipboard (fallback)!");
                            } catch (err) {
                                alert("Failed to copy. Please select the text manually.");
                            }
                            document.body.removeChild(textArea);
                        });
                    } else {
                        // Fallback for non-secure contexts (HTTP)
                        const textArea = document.createElement("textarea");
                        textArea.value = shareText;
                        document.body.appendChild(textArea);
                        textArea.select();
                        try {
                            document.execCommand('copy');
                            alert("Response copied to clipboard!");
                        } catch (err) {
                            alert("Failed to copy. Please select the text manually.");
                        }
                        document.body.removeChild(textArea);
                    }
                  }}
                  title="Copy for WhatsApp / Sharing"
                >
                  Share Response
                </button>
                <button className="close-btn" onClick={() => setSelectedTask(null)}>
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="task-modal-content">
              <div className="task-detail-row">
                <span className="label">Description:</span>
                <span className="value">{selectedTask.description}</span>
              </div>
              <div className="task-detail-row">
                <span className="label">Status:</span>
                <div style={{display: 'flex', alignItems: 'center', gap: '12px', flex: 1}}>
                  <span className={`status-badge ${selectedTask.status}`}>
                    {getStatusIcon(selectedTask.status)}
                    {selectedTask.status}
                  </span>
                  {(selectedTask.status === 'pending' || selectedTask.status === 'running') && (
                    <button 
                      className="cancel-btn"
                      onClick={() => {
                        handleCancel(selectedTask.id)
                        setSelectedTask({...selectedTask, status: 'cancelled'})
                      }}
                      style={{marginLeft: 'auto', padding: '4px 12px', fontSize: '12px'}}
                    >
                      Cancel Task
                    </button>
                  )}
                </div>
              </div>
              <div className="task-detail-row">
                <span className="label">Agent:</span>
                <span className="value">{selectedTask.agent_type || 'Auto'}</span>
              </div>
              <div className="task-detail-row">
                <span className="label">Created:</span>
                <span className="value">{new Date(selectedTask.created_at).toLocaleString()}</span>
              </div>
              {(() => {
                const model = selectedTask.model || (typeof selectedTask.result === 'object' && selectedTask.result?.model) || null
                const provider = selectedTask.provider || (typeof selectedTask.result === 'object' && selectedTask.result?.provider) || null
                const latency = selectedTask.latency_ms || (typeof selectedTask.result === 'object' && selectedTask.result?.latency_ms) || null
                const tokens = selectedTask.tokens_used || (typeof selectedTask.result === 'object' && selectedTask.result?.total_tokens) || null
                const isPaid = provider && provider !== 'ollama'
                return (
                  <>
                    {model && (
                      <div className="task-detail-row">
                        <span className="label">Model:</span>
                        <span className="value model-badge-display">
                          {model}
                          {isPaid && <span style={{color: '#f59e0b', marginLeft: 8, fontSize: 12}}>$ Paid</span>}
                          {!isPaid && provider && <span style={{color: '#10b981', marginLeft: 8, fontSize: 12}}>Free (Local)</span>}
                        </span>
                      </div>
                    )}
                    {provider && (
                      <div className="task-detail-row">
                        <span className="label">Provider:</span>
                        <span className="value" style={{textTransform: 'capitalize'}}>{provider}</span>
                      </div>
                    )}
                    {latency && (
                      <div className="task-detail-row">
                        <span className="label">Response Time:</span>
                        <span className="value">{(Number(latency) / 1000).toFixed(2)}s</span>
                      </div>
                    )}
                    {tokens && (
                      <div className="task-detail-row">
                        <span className="label">Tokens:</span>
                        <span className="value">{Number(tokens).toLocaleString()}</span>
                      </div>
                    )}
                  </>
                )
              })()}
              {selectedTask.error && (
                <div className="task-detail-row">
                  <span className="label" style={{color: '#ff4b4b'}}>Error:</span>
                  <span className="value" style={{color: '#ff4b4b'}}>{selectedTask.error}</span>
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
                          return <div key={i} className="bullet-point" dangerouslySetInnerHTML={{ __html: '• ' + line.trim().substring(2) }} />
                        }
                        // Handle numbered lists
                        if (/^\d+\./.test(line.trim())) {
                          return <div key={i} className="numbered-point" dangerouslySetInnerHTML={{ __html: line.trim() }} />
                        }
                        // Handle headers
                        if (line.trim().startsWith('# ')) {
                          return <h1 key={i} className="result-header" dangerouslySetInnerHTML={{ __html: line.trim().substring(2) }} />
                        }
                        if (line.trim().startsWith('## ')) {
                          return <h2 key={i} className="result-header" dangerouslySetInnerHTML={{ __html: line.trim().substring(3) }} />
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
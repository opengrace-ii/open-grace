import { useState, useEffect } from 'react'
import { Play, CheckCircle, XCircle, Clock, RotateCcw } from 'lucide-react'
import { APIClient } from '../api/client'
import './TaskList.css'

interface Task {
  id: string
  description: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  agent_type: string | null
  created_at: string
  result: any
}

interface TaskListProps {
  refreshTrigger?: number
}

export function TaskList({ refreshTrigger }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')

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
          <span>Status</span>
          <span>Created</span>
          <span>Actions</span>
        </div>

        {tasks.length === 0 ? (
          <div className="no-tasks">No tasks found</div>
        ) : (
          tasks.map((task) => (
            <div key={task.id} className="task-row">
              <div className="task-description" title={task.description}>
                {task.description}
              </div>
              <div className="task-agent">
                {task.agent_type || 'Auto'}
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
    </div>
  )
}
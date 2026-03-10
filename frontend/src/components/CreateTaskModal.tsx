import { useState } from 'react'
import { X, Send } from 'lucide-react'
import { APIClient } from '../api/client'
import './CreateTaskModal.css'

interface CreateTaskModalProps {
  onClose: () => void
  onCreated: () => void
}

const AGENT_TYPES = [
  { value: '', label: 'Auto (Best Match)' },
  { value: 'planner', label: 'Planner Agent' },
  { value: 'coder', label: 'Coder Agent' },
  { value: 'sysadmin', label: 'SysAdmin Agent' },
  { value: 'research', label: 'Research Agent' }
]

export function CreateTaskModal({ onClose, onCreated }: CreateTaskModalProps) {
  const [description, setDescription] = useState('')
  const [agentType, setAgentType] = useState('')
  const [priority, setPriority] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!description.trim()) return

    setError('')
    setLoading(true)

    try {
      await APIClient.createTask(description, agentType || undefined, priority)
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task')
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create New Task</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="description">Task Description</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what you want the AI to do..."
              rows={4}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="agentType">Agent Type</label>
              <select
                id="agentType"
                value={agentType}
                onChange={(e) => setAgentType(e.target.value)}
              >
                {AGENT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="priority">Priority (1-10)</label>
              <input
                id="priority"
                type="number"
                min={1}
                max={10}
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value))}
              />
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn-primary"
              disabled={loading || !description.trim()}
            >
              {loading ? 'Creating...' : (
                <>
                  <Send size={16} />
                  Create Task
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
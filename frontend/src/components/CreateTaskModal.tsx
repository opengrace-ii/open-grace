import { useState, useEffect } from 'react'
import { X, Send, Cpu, Zap, DollarSign } from 'lucide-react'
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

interface ModelInfo {
  id: string
  name: string
  provider: string
  type: 'free' | 'paid'
  description: string
}

const AVAILABLE_MODELS: ModelInfo[] = [
  { id: 'ollama-llama3', name: 'Llama 3', provider: 'Ollama (Local)', type: 'free', description: 'Free, runs locally' },
  { id: 'ollama-mistral', name: 'Mistral', provider: 'Ollama (Local)', type: 'free', description: 'Free, runs locally' },
  { id: 'gemini-flash', name: 'Gemini 1.5 Flash', provider: 'Google', type: 'paid', description: 'Fast & affordable' },
  { id: 'gemini-pro', name: 'Gemini 1.5 Pro', provider: 'Google', type: 'paid', description: 'Most capable' },
  { id: 'openai-gpt4', name: 'GPT-4', provider: 'OpenAI', type: 'paid', description: 'High quality' },
  { id: 'openai-gpt35', name: 'GPT-3.5 Turbo', provider: 'OpenAI', type: 'paid', description: 'Fast & cheap' },
]

export function CreateTaskModal({ onClose, onCreated }: CreateTaskModalProps) {
  const [description, setDescription] = useState('')
  const [agentType, setAgentType] = useState('')
  const [priority, setPriority] = useState(5)
  const [selectedModel, setSelectedModel] = useState('ollama-llama3')
  const [modelFilter, setModelFilter] = useState<'all' | 'free' | 'paid'>('all')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!description.trim()) return

    setError('')
    setLoading(true)

    try {
      await APIClient.createTask(description, agentType || undefined, priority, selectedModel)
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

          {/* Model Selection */}
          <div className="form-group model-selection">
            <label>AI Model</label>
            <div className="model-tabs">
              <button 
                type="button"
                className={`model-tab ${modelFilter === 'all' ? 'active' : ''}`}
                onClick={() => setModelFilter('all')}
              >
                All
              </button>
              <button 
                type="button"
                className={`model-tab ${modelFilter === 'free' ? 'active' : ''}`}
                onClick={() => setModelFilter('free')}
              >
                <Cpu size={14} />
                Free (Local)
              </button>
              <button 
                type="button"
                className={`model-tab ${modelFilter === 'paid' ? 'active' : ''}`}
                onClick={() => setModelFilter('paid')}
              >
                <Zap size={14} />
                Paid (API)
              </button>
            </div>
            <div className="model-list">
              {AVAILABLE_MODELS
                .filter(m => modelFilter === 'all' || m.type === modelFilter)
                .map((model) => (
                <div 
                  key={model.id}
                  className={`model-option ${selectedModel === model.id ? 'selected' : ''}`}
                  onClick={() => setSelectedModel(model.id)}
                >
                  <div className="model-info">
                    <span className="model-name">{model.name}</span>
                    <span className="model-provider">{model.provider}</span>
                    <span className="model-desc">{model.description}</span>
                  </div>
                  <div className="model-badge">
                    {model.type === 'free' ? (
                      <span className="badge free"><Cpu size={12} /> Free</span>
                    ) : (
                      <span className="badge paid"><DollarSign size={12} /> Paid</span>
                    )}
                  </div>
                </div>
              ))}
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
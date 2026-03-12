import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Send, Cpu, Zap, ChevronRight } from 'lucide-react';
import { APIClient } from '../api/client';
import './CreateTaskModal.css';

interface CreateTaskModalProps {
  onClose: () => void;
  onCreated: () => void;
}

const AGENT_TYPES = [
  { value: 'auto', label: 'Auto (Best Match)' },
  { value: 'planner', label: 'Planner Agent' },
  { value: 'coder', label: 'Coder Agent' },
  { value: 'sysadmin', label: 'SysAdmin Agent' },
  { value: 'research', label: 'Research Agent' }
];

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  type: 'free' | 'paid';
  description: string;
}

const AVAILABLE_MODELS: ModelInfo[] = [
  { id: 'ollama-llama3', name: 'Llama 3', provider: 'Ollama (Local)', type: 'free', description: 'Free, runs locally' },
  { id: 'ollama-mistral', name: 'Mistral', provider: 'Ollama (Local)', type: 'free', description: 'Free, runs locally' },
  { id: 'gemini-flash', name: 'Gemini 1.5 Flash', provider: 'Google', type: 'paid', description: 'Fast & affordable' },
  { id: 'gemini-pro', name: 'Gemini 1.5 Pro', provider: 'Google', type: 'paid', description: 'Most capable' },
  { id: 'openai-gpt4', name: 'GPT-4', provider: 'OpenAI', type: 'paid', description: 'High quality' },
];

export function CreateTaskModal({ onClose, onCreated }: CreateTaskModalProps) {
  // --- Form State ---
  const [description, setDescription] = useState('');
  const [agentType, setAgentType] = useState('auto');
  const [priority, setPriority] = useState(5);
  const [selectedModel, setSelectedModel] = useState('ollama-llama3');
  const [modelFilter, setModelFilter] = useState<'all' | 'free' | 'paid'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // --- Resizing & Positioning State ---
  const modalRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 550, height: 750 });
  const [pos, setPos] = useState({ x: 0, y: 0 }); // Center by default
  const isResizing = useRef<string | null>(null);
  const initialMousePos = useRef({ x: 0, y: 0 });
  const initialSize = useRef({ width: 0, height: 0 });
  const initialPos = useRef({ x: 0, y: 0 });

  // Center modal on mount
  useEffect(() => {
    const x = (window.innerWidth - size.width) / 2;
    const y = (window.innerHeight - size.height) / 2;
    setPos({ x, y });
  }, []);

  const handleMouseDown = (e: React.MouseEvent, direction: string) => {
    isResizing.current = direction;
    initialMousePos.current = { x: e.clientX, y: e.clientY };
    initialSize.current = { ...size };
    initialPos.current = { ...pos };
    e.preventDefault();
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing.current) return;

    const dx = e.clientX - initialMousePos.current.x;
    const dy = e.clientY - initialMousePos.current.y;
    const dir = isResizing.current;

    let newWidth = initialSize.current.width;
    let newHeight = initialSize.current.height;
    let newX = initialPos.current.x;
    let newY = initialPos.current.y;

    const minW = 400;
    const minH = 500;

    if (dir.includes('right')) newWidth = Math.max(minW, initialSize.current.width + dx);
    if (dir.includes('left')) {
      const targetWidth = initialSize.current.width - dx;
      if (targetWidth > minW) {
        newWidth = targetWidth;
        newX = initialPos.current.x + dx;
      }
    }
    if (dir.includes('bottom')) newHeight = Math.max(minH, initialSize.current.height + dy);
    if (dir.includes('top')) {
      const targetHeight = initialSize.current.height - dy;
      if (targetHeight > minH) {
        newHeight = targetHeight;
        newY = initialPos.current.y + dy;
      }
    }

    setSize({ width: newWidth, height: newHeight });
    setPos({ x: newX, y: newY });
  }, []);

  const handleMouseUp = useCallback(() => {
    isResizing.current = null;
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || loading) return;

    setError('');
    setLoading(true);

    try {
      await APIClient.createTask(description, agentType === 'auto' ? undefined : agentType, priority, selectedModel);
      await APIClient.logActivity(`Created Task: "${description.substring(0, 30)}..."`, 'Task', `Agent: ${agentType}, Model: ${selectedModel}`);
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div 
        ref={modalRef}
        style={{ 
          width: `${size.width}px`, 
          height: `${size.height}px`,
          transform: `translate(${pos.x}px, ${pos.y}px)`,
          position: 'absolute',
          top: 0,
          left: 0
        }}
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        {/* --- Resize Handles --- */}
        <div className="resize-handle handle-top" onMouseDown={(e) => handleMouseDown(e, 'top')} />
        <div className="resize-handle handle-bottom" onMouseDown={(e) => handleMouseDown(e, 'bottom')} />
        <div className="resize-handle handle-left" onMouseDown={(e) => handleMouseDown(e, 'left')} />
        <div className="resize-handle handle-right" onMouseDown={(e) => handleMouseDown(e, 'right')} />
        
        <div className="resize-handle handle-top-left" onMouseDown={(e) => handleMouseDown(e, 'topleft')} />
        <div className="resize-handle handle-top-right" onMouseDown={(e) => handleMouseDown(e, 'topright')} />
        <div className="resize-handle handle-bottom-left" onMouseDown={(e) => handleMouseDown(e, 'bottomleft')} />
        <div className="resize-handle handle-bottom-right" onMouseDown={(e) => handleMouseDown(e, 'bottomright')} />

        {/* --- Header --- */}
        <div className="modal-header">
          <h2>Create New Task</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* --- Body (Scrollable) --- */}
        <div className="modal-body custom-scrollbar">
          {/* Task Description */}
          <div className="form-group">
            <label className="field-label">Task Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what you want the AI to do..."
              className="text-area"
            />
          </div>

          {/* Settings Row */}
          <div className="settings-row">
            <div className="form-group">
              <label className="field-label">Agent Type</label>
              <div className="select-wrapper">
                <select
                  value={agentType}
                  onChange={(e) => setAgentType(e.target.value)}
                  className="custom-select"
                >
                  {AGENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                <div className="select-icon">
                  <ChevronRight size={14} style={{ transform: 'rotate(90deg)' }} />
                </div>
              </div>
            </div>
            <div className="form-group">
              <label className="field-label">Priority (1-10)</label>
              <input
                type="number"
                min={1} max={10}
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value))}
                className="number-input"
              />
            </div>
          </div>

          {/* AI Model Selection */}
          <div className="form-group">
            <label className="field-label">AI Model</label>
            
            {/* Tabs */}
            <div className="model-tabs">
              {(['all', 'free', 'paid'] as const).map(tab => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setModelFilter(tab)}
                  className={`tab-btn ${modelFilter === tab ? 'active' : ''}`}
                >
                  {tab === 'free' && <Cpu size={12} />}
                  {tab === 'paid' && <Zap size={12} />}
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {/* Scrollable Card List */}
            <div className="model-list custom-scrollbar">
              {AVAILABLE_MODELS
                .filter(m => modelFilter === 'all' || m.type === modelFilter)
                .map((model) => (
                <div 
                  key={model.id}
                  onClick={() => setSelectedModel(model.id)}
                  className={`model-card ${selectedModel === model.id ? 'selected' : ''}`}
                >
                  <div className="model-card-header">
                    <div>
                      <div className="model-title">{model.name}</div>
                      <div className="model-provider">{model.provider}</div>
                    </div>
                    {model.type === 'free' && (
                       <div className="free-badge">
                         <Cpu size={10} /> Free
                       </div>
                    )}
                  </div>
                  <div className="model-description">{model.description}</div>
                </div>
              ))}
            </div>
          </div>
          
          {error && <div className="error-box">{error}</div>}
        </div>

        {/* --- Footer --- */}
        <div className="modal-footer">
          <button type="button" className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button 
            type="submit" 
            onClick={handleSubmit}
            disabled={loading || !description.trim()}
            className="submit-btn"
          >
            <Send size={16} />
            {loading ? 'Creating...' : 'Create Task'}
          </button>
        </div>
      </div>
    </div>
  );
}
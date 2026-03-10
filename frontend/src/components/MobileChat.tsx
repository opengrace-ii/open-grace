import { useState, useRef, useEffect } from 'react'
import { Send, Menu, MoreVertical, Paperclip, Mic, Bot, User, Check, CheckCheck, LogOut, Trash2 } from 'lucide-react'
import { APIClient } from '../api/client'
import './MobileChat.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  status?: 'sending' | 'sent' | 'error'
}

interface TaskSuggestion {
  id: string
  title: string
  icon: string
}

const QUICK_ACTIONS: TaskSuggestion[] = [
  { id: '1', title: 'Review code', icon: 'code' },
  { id: '2', title: 'Explain error', icon: 'bug' },
  { id: '3', title: 'Write tests', icon: 'test' },
  { id: '4', title: 'Optimize', icon: 'zap' },
]

const STORAGE_KEY = 'opengrace_mobile_chat_history'

export function MobileChat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    // Load from localStorage on init
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        return parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        }))
      } catch {
        return []
      }
    }
    return []
  })
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showQuickActions, setShowQuickActions] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Save messages to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    // Hide quick actions if we have messages
    if (messages.length > 0) {
      setShowQuickActions(false)
    }
  }, [messages])

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      status: 'sent'
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setShowQuickActions(false)

    // Add assistant placeholder
    const assistantId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      status: 'sending'
    }])

    try {
      // Create a task for the AI
      const response = await APIClient.createTask(content.trim())
      const taskId = response.id
      
      // Poll for task completion
      let attempts = 0
      const maxAttempts = 60 // 60 seconds timeout
      
      const pollInterval = setInterval(async () => {
        try {
          const taskStatus = await APIClient.getTaskStatus(taskId)
          attempts++
          
          if (taskStatus.status === 'completed' && taskStatus.result) {
            clearInterval(pollInterval)
            const result = typeof taskStatus.result === 'string' 
              ? taskStatus.result 
              : JSON.stringify(taskStatus.result, null, 2)
            
            setMessages(prev => prev.map(msg => 
              msg.id === assistantId 
                ? { ...msg, content: result, status: 'sent' }
                : msg
            ))
            setIsLoading(false)
          } else if (taskStatus.status === 'failed') {
            clearInterval(pollInterval)
            setMessages(prev => prev.map(msg => 
              msg.id === assistantId 
                ? { ...msg, content: 'Task failed: ' + (taskStatus.error || 'Unknown error'), status: 'error' }
                : msg
            ))
            setIsLoading(false)
          } else if (attempts >= maxAttempts) {
            clearInterval(pollInterval)
            setMessages(prev => prev.map(msg => 
              msg.id === assistantId 
                ? { ...msg, content: 'Task is taking longer than expected. Check the dashboard for results.', status: 'sent' }
                : msg
            ))
            setIsLoading(false)
          }
        } catch (pollError) {
          clearInterval(pollInterval)
          setMessages(prev => prev.map(msg => 
            msg.id === assistantId 
              ? { ...msg, content: 'Error checking task status. Please check the dashboard.', status: 'error' }
              : msg
          ))
          setIsLoading(false)
        }
      }, 1000) // Poll every second
      
    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === assistantId 
          ? { ...msg, content: 'Sorry, I encountered an error. Please try again.', status: 'error' }
          : msg
      ))
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleQuickAction = (action: TaskSuggestion) => {
    const prompts: Record<string, string> = {
      'code': 'Please review my code for best practices and potential issues:',
      'bug': 'I\'m getting an error. Can you help me understand and fix it?',
      'test': 'Please write unit tests for the following code:',
      'zap': 'Please optimize this code for better performance:',
    }
    setInput(prompts[action.icon] || action.title)
    inputRef.current?.focus()
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const clearHistory = () => {
    if (confirm('Clear all chat history?')) {
      setMessages([])
      setShowQuickActions(true)
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  const handleLogout = () => {
    if (confirm('Logout from this device?')) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login?logout=true'
    }
  }
  
  const handleLogoutAll = () => {
    if (confirm('Logout from ALL devices? This will terminate all your sessions.')) {
      // Call API to terminate all sessions
      fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/sessions/terminate-all`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      }).finally(() => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login?logout=all'
      })
    }
  }

  return (
    <div className="mobile-chat">
      {/* Header */}
      <header className="mobile-header">
        <button className="icon-btn" onClick={clearHistory} title="Clear History">
          <Trash2 size={20} />
        </button>
        <div className="header-title">
          <Bot size={20} />
          <span>Open Grace</span>
        </div>
        <button className="icon-btn logout-btn" onClick={handleLogout} title="Logout">
          <LogOut size={20} />
        </button>
      </header>

      {/* Welcome Screen or Messages */}
      {messages.length === 0 ? (
        <div className="welcome-screen">
          <div className="welcome-icon">
            <Bot size={48} />
          </div>
          <h2>How can I help you today?</h2>
          <p>Chat with AI agents to code, review, and automate tasks</p>
          
          <div className="quick-actions">
            {QUICK_ACTIONS.map(action => (
              <button
                key={action.id}
                className="quick-action-btn"
                onClick={() => handleQuickAction(action)}
              >
                {action.title}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="messages-container" ref={messagesContainerRef}>
          {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.role} ${message.status || ''}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className="message-content">
              <div className="message-text">{message.content}</div>
              <div className="message-meta">
                <span className="message-time">{formatTime(message.timestamp)}</span>
                {message.role === 'user' && message.status === 'sent' && (
                  <CheckCheck size={14} className="read-receipt" />
                )}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="typing-indicator">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        )}

        <div ref={messagesEndRef} />
        </div>
      )}

      {/* Input Area */}
      <form className="input-container" onSubmit={handleSubmit}>
        <button type="button" className="attach-btn">
          <Paperclip size={24} />
        </button>
        
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Open Grace..."
            disabled={isLoading}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck="false"
          />
        </div>

        {input.trim() ? (
          <button 
            type="submit" 
            className="send-btn"
            disabled={isLoading}
          >
            <Send size={24} />
          </button>
        ) : (
          <button type="button" className="mic-btn">
            <Mic size={24} />
          </button>
        )}
      </form>
    </div>
  )
}
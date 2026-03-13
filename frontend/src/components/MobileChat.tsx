import { useState, useRef, useEffect } from 'react'
import { 
  Send, 
  Mic, 
  Bot, 
  CheckCheck, 
  LogOut, 
  Trash2, 
  Code,
  Bug,
  TestTube,
  Zap,
  ListTodo,
  MessageSquare
} from 'lucide-react'
import { APIClient } from '../api/client'
import { TaskList } from './TaskList'
import { Logo } from './Logo'
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
  icon: 'code' | 'bug' | 'test' | 'zap'
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
  const [isRecording, setIsRecording] = useState(false)
  const [activeView, setActiveView] = useState<'chat' | 'tasks'>(() => {
    const path = window.location.pathname.substring(1)
    return path === 'tasks' ? 'tasks' : 'chat'
  })
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<any>(null)

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = false
      recognitionRef.current.lang = 'en-US'

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        setInput(prev => prev + (prev ? ' ' : '') + transcript)
        setIsRecording(false)
      }

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error', event.error)
        setIsRecording(false)
      }

      recognitionRef.current.onend = () => {
        setIsRecording(false)
      }
    }
  }, [])

  // Save messages to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }, [messages])

  // Handle auto-expanding textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [input])

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser.')
      return
    }

    if (isRecording) {
      recognitionRef.current.stop()
    } else {
      setIsRecording(true)
      recognitionRef.current.start()
    }
  }

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

    const assistantId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      status: 'sending'
    }])

    try {
      const response = await APIClient.createTask(content.trim())
      const taskId = response.id
      
      let attempts = 0
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
          } else if (attempts >= 60) {
            clearInterval(pollInterval)
            setMessages(prev => prev.map(msg => 
              msg.id === assistantId 
                ? { ...msg, content: 'Still processing... Visit the dashboard for more info.', status: 'sent' }
                : msg
            ))
            setIsLoading(false)
          }
        } catch (err) {
          clearInterval(pollInterval)
          setIsLoading(false)
        }
      }, 1000)
    } catch (err) {
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
    const prompt = prompts[action.icon] || action.title
    sendMessage(prompt)
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const clearHistory = () => {
    if (confirm('Clear all chat history?')) {
      setMessages([])
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  const handleLogout = () => {
    if (confirm('Logout?')) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login?logout=true'
    }
  }

  const getActionIcon = (icon: string) => {
    switch (icon) {
      case 'code': return <Code size={20} />
      case 'bug': return <Bug size={20} />
      case 'test': return <TestTube size={20} />
      case 'zap': return <Zap size={20} />
      default: return <Bot size={20} />
    }
  }

  return (
    <div className="mobile-chat">
      <header className="mobile-header">
        <div className="header-title">
          <Logo width={40} />
          <div className="header-info">
            <span>Open Grace</span>
            <span className="status">{activeView === 'chat' ? 'online' : 'tasks view'}</span>
          </div>
        </div>
        <div className="header-actions">
          <button className="header-icon-btn" onClick={clearHistory} title="Clear View"><Trash2 size={20} /></button>
          <button className="header-icon-btn" onClick={handleLogout} title="Logout"><LogOut size={20} /></button>
        </div>
      </header>

      <div className="mobile-content-area">
        {activeView === 'chat' ? (
          <>
            {messages.length === 0 ? (
              <div className="welcome-screen">
                <div className="welcome-icon">
                  <Logo width={120} />
                </div>
                <h2>How can I help you?</h2>
                <p>Talk to me or choose a quick action below to start an AI task.</p>
                
                <div className="quick-actions">
                  {QUICK_ACTIONS.map(action => (
                    <button
                      key={action.id}
                      className="quick-action-btn"
                      onClick={() => handleQuickAction(action)}
                    >
                      {getActionIcon(action.icon)}
                      {action.title}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="messages-container" ref={messagesContainerRef}>
                {messages.map((message) => (
                  <div key={message.id} className={`message ${message.role}`}>
                    <div className="message-text">{message.content}</div>
                    <div className="message-meta">
                      <span className="message-time">{formatTime(message.timestamp)}</span>
                      {message.role === 'user' && (
                        <CheckCheck size={14} className="read-receipt" />
                      )}
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

            <form className="input-container" onSubmit={handleSubmit}>
              <div className="input-pill">
                <textarea
                  ref={textareaRef}
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Message"
                  disabled={isLoading}
                />
              </div>

              {input.trim() || isLoading ? (
                <button type="submit" className="action-btn send-btn" disabled={isLoading || !input.trim()}>
                  <Send size={20} />
                </button>
              ) : (
                <button 
                  type="button" 
                  className={`action-btn mic-btn ${isRecording ? 'recording' : ''}`}
                  onClick={toggleRecording}
                >
                  <Mic size={20} />
                </button>
              )}
            </form>
          </>
        ) : (
          <div className="mobile-tasks-view">
            <TaskList />
          </div>
        )}
      </div>

      <nav className="mobile-nav">
        <button 
          className={`nav-item ${activeView === 'chat' ? 'active' : ''}`}
          onClick={() => {
            setActiveView('chat')
            window.history.pushState(null, '', '/')
          }}
        >
          <MessageSquare size={20} />
          <span>Chat</span>
        </button>
        <button 
          className={`nav-item ${activeView === 'tasks' ? 'active' : ''}`}
          onClick={() => {
            setActiveView('tasks')
            window.history.pushState(null, '', '/tasks')
          }}
        >
          <ListTodo size={20} />
          <span>Tasks</span>
        </button>
      </nav>
    </div>
  )
}
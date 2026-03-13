import { useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { APIClient } from '../api/client'
import { Logo } from './Logo'
import './Login.css'

interface LoginProps {
  onLogin: (token: string) => void
}

export function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await APIClient.login(username)
      onLogin(response.access_token)
    } catch (err) {
      console.error('Login error:', err)
      if (err instanceof Error) {
        setError(err.message)
      } else if (typeof err === 'string') {
        setError(err)
      } else {
        setError('Login failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* Left side - Content */}
      <div className="login-content">
        <div className="login-brand">
          <Logo width={48} />
          <span className="brand-title">Open Grace</span>
        </div>
        
        <h1 className="login-headline">
          Your Private, Local
          <br />
          <span className="gradient-text">AI Engineer Team</span>
        </h1>
        
        <p className="login-description">
          Powered by TaskForge. Run autonomous agents for coding, DevOps, 
          research, and automation—all using local LLMs via Ollama.
        </p>
        
        <div className="login-features">
          <div className="login-feature">
            <span className="feature-dot"></span>
            <span>4 AI Agents: Planner, Coder, SysAdmin, Researcher</span>
          </div>
          <div className="login-feature">
            <span className="feature-dot"></span>
            <span>Docker Sandbox for secure execution</span>
          </div>
          <div className="login-feature">
            <span className="feature-dot"></span>
            <span>AES-256 encrypted secret vault</span>
          </div>
          <div className="login-feature">
            <span className="feature-dot"></span>
            <span>RAG-powered knowledge retrieval</span>
          </div>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="login-form-container">
        <div className="login-box">
          <div className="login-header">
            <Logo width={120} className="login-logo-large" />
            <h2>Welcome to Open Grace</h2>
            <p>Enter your username to access your AI team</p>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                autoFocus
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" disabled={loading} className="login-btn">
              {loading ? 'Signing in...' : (
                <>
                  Sign In
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <div className="login-hint">
            <p>Demo: Enter any username to login</p>
          </div>
        </div>
      </div>
    </div>
  )
}
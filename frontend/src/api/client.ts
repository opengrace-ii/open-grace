// Use environment variable or detect if running on mobile
// Use environment variable or detect if running on mobile
const getApiUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl) return envUrl
  
  // Dynamic host detection
  const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'https:' : 'http:'
  
  if (host !== 'localhost' && host !== '127.0.0.1') {
    return `${protocol}//${host}:8000`
  }
  
  // If accessing from mobile device, use network IP
  if (typeof navigator !== 'undefined' && /Mobi|Android/i.test(navigator.userAgent)) {
    return 'http://192.168.0.165:8000'
  }
  
  return 'http://localhost:8000'
}

export const API_BASE_URL = getApiUrl()

export class APIClient {
  private static token: string | null = null

  static setToken(token: string | null) {
    this.token = token
  }

  static async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(url, {
      ...options,
      headers
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      const errorMessage = typeof error.detail === 'string' ? error.detail : 
                          typeof error.message === 'string' ? error.message :
                          JSON.stringify(error.detail || error.message || error)
      throw new Error(errorMessage || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Auth
  static async login(username: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username })
    })
  }

  static async getCurrentUser() {
    return this.request('/auth/me')
  }

  // Tasks
  static async getTasks(status?: string) {
    const params = status ? `?status=${status}` : ''
    return this.request(`/tasks${params}`)
  }

  static async createTask(description: string, agentType?: string, priority: number = 5, model?: string) {
    return this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify({ description, agent_type: agentType, priority, model })
    })
  }

  static async cancelTask(taskId: string) {
    return this.request(`/tasks/${taskId}/cancel`, { method: 'POST' })
  }

  static async getTaskStatus(taskId: string) {
    return this.request(`/tasks/${taskId}`)
  }

  // Agents
  static async getAgents() {
    return this.request('/agents')
  }

  // System
  static async getSystemStatus() {
    return this.request('/system/status')
  }

  static async getProviders() {
    return this.request('/system/providers')
  }

  // Sessions
  static async getSessions() {
    return this.request('/auth/sessions')
  }

  static async terminateAllSessions() {
    return this.request('/auth/sessions/terminate-all', { method: 'POST' })
  }

  static async terminateSession(sessionId: string) {
    return this.request(`/auth/sessions/${sessionId}`, { method: 'DELETE' })
  }

  // Observability
  static async logActivity(event: string, category: string = 'UI', details?: string) {
    try {
      await this.request('/observability/activity', {
        method: 'POST',
        body: JSON.stringify({ event, category, details })
      })
    } catch {
      // Silently fail - don't break the UI for logging
    }
  }
}
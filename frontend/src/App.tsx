import { useState, useEffect } from 'react'
import { Dashboard } from './components/Dashboard'
import { Login } from './components/Login'
import { MobileChat } from './components/MobileChat'
import { LandingPage } from './components/LandingPage'
import { APIClient } from './api/client'
import './App.css'

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    if (token) {
      APIClient.setToken(token)
      setIsAuthenticated(true)
    }
    
    // Detect mobile device
    const checkMobile = () => {
      const isMobileDevice = window.innerWidth < 768 || 
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
      setIsMobile(isMobileDevice)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then(() => console.log('Service Worker registered'))
        .catch(() => console.log('Service Worker registration failed'))
    }
    
    return () => window.removeEventListener('resize', checkMobile)
  }, [token])

  const handleLogin = (newToken: string) => {
    localStorage.setItem('token', newToken)
    APIClient.setToken(newToken)
    setToken(newToken)
    setIsAuthenticated(true)
    
    // Redirect to root to clear /login from URL and show Dashboard
    if (window.location.pathname === '/login' || window.location.search.includes('login')) {
      window.history.pushState({}, '', '/')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    APIClient.setToken(null)
    setToken(null)
    setIsAuthenticated(false)
  }

  // Check if we're on the landing page route
  const isLandingPage = window.location.pathname === '/' && !window.location.search.includes('login')
  // Check if explicitly on login page
  const isLoginPage = window.location.pathname === '/login' || window.location.search.includes('login')

  return (
    <div className="app">
      {isAuthenticated && !isLoginPage ? (
        isMobile ? <MobileChat /> : <Dashboard onLogout={handleLogout} />
      ) : isLandingPage ? (
        <LandingPage />
      ) : (
        <Login onLogin={handleLogin} />
      )}
    </div>
  )
}

export default App
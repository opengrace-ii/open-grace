import { useState } from 'react'
import { 
  Terminal, 
  Copy, 
  Check, 
  Cpu, 
  Shield, 
  Zap, 
  Database,
  GitBranch,
  Box,
  ChevronRight,
  Github,
  MessageSquare,
  Lock,
  Server,
  Sparkles,
  Cloud,
  Puzzle,
  Code,
  Terminal as TerminalIcon,
  Globe
} from 'lucide-react'
import './LandingPage.css'

export function LandingPage() {
  const [copied, setCopied] = useState(false)

  const installCommand = 'git clone https://github.com/opengrace-ii/open-grace && cd open-grace && pip install -e .'

  const handleCopy = () => {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(installCommand).then(() => {
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }).catch(() => {
        copyFallback(installCommand)
      })
    } else {
      copyFallback(installCommand)
    }

    function copyFallback(text: string) {
      const textArea = document.createElement("textarea")
      textArea.value = text
      textArea.style.position = "fixed"
      textArea.style.left = "-9999px"
      textArea.style.top = "0"
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      try {
        document.execCommand('copy')
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      } catch (err) {
        console.error('Fallback copy failed', err)
      }
      document.body.removeChild(textArea)
    }
  }

  const pillars = [
    {
      icon: <Cpu size={32} />,
      title: 'TaskForge Engine',
      subtitle: 'The Brain',
      description: 'AI process manager that orchestrates specialized agents (Coder, Planner, Research, DevOps) for complex multi-step tasks.',
      features: [
        { label: 'Agent Orchestration', desc: 'Coordinates collaboration between multiple AI agents' },
        { label: 'Tool Execution', desc: 'Secure, permission-gated runtime for real-world actions' },
        { label: 'Local LLM Integration', desc: 'Connects to Ollama for privacy-first AI reasoning' },
        { label: 'Structured Planning', desc: 'Converts prompts into actionable task graphs' }
      ]
    },
    {
      icon: <Cloud size={32} />,
      title: 'Grace Cloud',
      subtitle: 'Distributed Scale',
      description: 'Run your AI team across multiple machines for true parallel processing and horizontal scaling.',
      features: [
        { label: 'Distributed Workers', desc: 'Deploy on GPU machines or home servers' },
        { label: 'Message Bus', desc: 'Secure agent communication via Redis/NATS' },
        { label: 'Kubernetes Ready', desc: 'Production-grade cloud deployment' }
      ]
    },
    {
      icon: <Puzzle size={32} />,
      title: 'Grace Plugins',
      subtitle: 'The Ecosystem',
      description: 'Extend capabilities with a developer-friendly plugin system for DevOps, coding, research, and system tools.',
      features: [
        { label: 'DevOps Tools', desc: 'Docker, K8s, AWS integration' },
        { label: 'Coding Tools', desc: 'Python runner, Git, linters' },
        { label: 'Research Tools', desc: 'Web search, API calls, scraping' },
        { label: 'System Tools', desc: 'Filesystem, shell, database access' }
      ]
    },
    {
      icon: <Shield size={32} />,
      title: 'Security First',
      subtitle: 'Built on Trust',
      description: 'Every AI action is treated as potentially dangerous and isolated by default.',
      features: [
        { label: 'Docker Sandbox', desc: 'Isolated, disposable containers' },
        { label: 'Permission Gating', desc: 'Human approval for critical actions' },
        { label: 'Secret Vault', desc: 'AES-256 encrypted credential storage' },
        { label: 'Tool Allowlisting', desc: 'Strict boundary on AI authority' }
      ]
    }
  ]

  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="nav-brand">
          <span className="brand-icon">◈</span>
          <span className="brand-title">Open Grace</span>
        </div>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="https://github.com/opengrace-ii" target="_blank" rel="noopener">
            <Github size={18} />
            GitHub
          </a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-badge">
          <span className="pulse-dot"></span>
          AI Operating System
        </div>
        
        <h1 className="hero-title">
          Open Grace:
          <br />
          <span className="gradient-text">The AI Operating System</span>
          <br />
          for Autonomous Agents
        </h1>
        
        <p className="hero-tagline">TaskForge Inside.</p>
        
        <p className="hero-description">
          Your Private, Local AI Engineer Team. Powered by Ollama.
        </p>
        
        <p className="hero-body">
          Open Grace is a modular, open-source platform that transforms your local machine into an AI Operating System. 
          By combining the powerful TaskForge agent engine with a secure, plug-and-play ecosystem, Open Grace allows you 
          to run, manage, and coordinate a swarm of autonomous agents for coding, DevOps, research, and automation—all 
          using local LLMs via Ollama. Get the power of an AI team without sending data to the cloud.
        </p>

        <div className="hero-actions">
          <a href="/login" className="btn-primary">
            <Sparkles size={18} />
            Get Started with Open Grace (Free)
            <ChevronRight size={18} />
          </a>
        </div>

        {/* Install Box */}
        <div className="install-section">
          <div className="install-label">Quick Install</div>
          <div className="install-box">
            <Terminal size={16} className="command-icon" />
            <code>git clone https://github.com/opengrace-ii/open-grace</code>
            <button className="copy-btn" onClick={handleCopy}>
              {copied ? <Check size={16} /> : <Copy size={16} />}
            </button>
          </div>
        </div>
      </section>

      {/* Pillars Section */}
      <section className="pillars-section" id="features">
        <div className="section-header">
          <h2>Key Features and Pillars</h2>
          <p>Everything you need to build your AI team</p>
        </div>
        
        <div className="pillars-grid">
          {pillars.map((pillar, idx) => (
            <div key={idx} className="pillar-card">
              <div className="pillar-header">
                <div className="pillar-icon">{pillar.icon}</div>
                <div className="pillar-titles">
                  <h3>{pillar.title}</h3>
                  <span className="pillar-subtitle">{pillar.subtitle}</span>
                </div>
              </div>
              <p className="pillar-description">{pillar.description}</p>
              <div className="pillar-features">
                {pillar.features.map((feature, fidx) => (
                  <div key={fidx} className="feature-item">
                    <span className="feature-label">{feature.label}</span>
                    <span className="feature-desc">{feature.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* SDK Section */}
      <section className="sdk-section">
        <div className="sdk-content">
          <div className="sdk-text">
            <h2>Open Grace Developer SDK</h2>
            <p>Build the next generation of autonomous agents and tools.</p>
            <div className="sdk-features">
              <div className="sdk-feature">
                <Code size={20} />
                <span>Agent Base Class for specialized agents</span>
              </div>
              <div className="sdk-feature">
                <Puzzle size={20} />
                <span>Simple Python class for new tools</span>
              </div>
              <div className="sdk-feature">
                <Server size={20} />
                <span>Model Connector for local LLMs</span>
              </div>
              <div className="sdk-feature">
                <MessageSquare size={20} />
                <span>Message Bus API for agent communication</span>
              </div>
            </div>
          </div>
          <div className="sdk-code">
            <div className="code-header">
              <span>agent.py</span>
            </div>
            <pre><code>{`from grace_sdk import GraceAgent, Tool

class CodeReviewer(GraceAgent):
    def plan(self, diff):
        # Uses Ollama for reasoning
        return self.model.review(diff)
    
    def execute(self, task):
        # Secure execution
        return self.run_tool('git', task)`}</code></pre>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to command your own AI engineer team?</h2>
          <div className="requirements">
            <span>Requirements:</span> Python 3.10+, Docker, Ollama
          </div>
          <div className="cta-steps">
            <div className="step">
              <span className="step-num">1</span>
              <code>git clone https://github.com/opengrace-ii/open-grace</code>
            </div>
            <div className="step">
              <span className="step-num">2</span>
              <code>cd open-grace && pip install -e .</code>
            </div>
            <div className="step">
              <span className="step-num">3</span>
              <code>grace init && grace start</code>
            </div>
          </div>
          <a href="/login" className="btn-primary large">
            <Sparkles size={20} />
            Launch Open Grace
            <ChevronRight size={20} />
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="brand-icon">◈</span>
            <span>Open Grace</span>
          </div>
          <p className="footer-tagline">
            Autonomous. Private. Powerful.
          </p>
        </div>
        <div className="footer-bottom">
          <p>© 2026 Open Grace. MIT License.</p>
        </div>
      </footer>
    </div>
  )
}
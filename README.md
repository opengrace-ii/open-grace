# Open Grace

### The AI Operating System

Open-source Agent OS built in Python. 20K+ LOC. 4 AI Agents. Docker Sandbox. Local LLM First.
One platform. Private. Autonomous. Agents that actually work for you.

[Documentation](https://github.com/opengrace-ii/open-grace/wiki) •
[Quick Start](#quick-start) •
[GitHub](https://github.com/opengrace-ii)

---

> **v1.0.0** — Production Ready Release (March 2026)
> 
> Open Grace is feature-complete and production-ready. Built for developers who want AI that actually gets things done — running locally on your hardware with enterprise-grade security.

---

## What is Open Grace?

Open Grace is an open-source **AI Operating System** — not a chatbot framework, not a simple Python wrapper around an LLM. It is a full operating system for autonomous agents, built from the ground up in Python.

Traditional agent frameworks wait for you to type something. Open Grace runs **autonomous agents that work for you** — on schedules, 24/7, building knowledge graphs, executing code, managing deployments, and reporting results to your dashboard.

The entire system runs locally using **Ollama** for maximum privacy. No data leaves your machine unless you explicitly configure it.

```bash
# Quick Install (requires Python 3.10+, Docker, Ollama)
git clone https://github.com/opengrace-ii/open-grace
cd open-grace

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Open Grace
pip install -e .

# Initialize and start
grace init
grace start

# Dashboard live at http://localhost:5173
```

---

## TaskForge: The Core AI Agent Engine (The Brain)

TaskForge is the heart of Open Grace, functioning as the dedicated AI process manager and orchestrator.

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Agent Orchestration** | Manages the lifecycle of specialized agents (Coder, Planner, Research, DevOps) and coordinates their collaboration. | Runs complex, multi-step tasks that one agent cannot handle alone. |
| **Tool Execution Runtime** | Provides a secure, permission-gated runtime for agents to interact with the real world (files, shell, Git, Docker). | Allows AI to take meaningful actions, not just talk. |
| **Local LLM Integration** | Seamless connection to local models (llama3, mistral, deepseek) via Ollama, ensuring privacy and low latency. | Maximum data privacy and no token costs for AI reasoning. |
| **Structured Planning** | Converts complex user prompts into step-by-step, actionable task graphs using model reasoning. | Ensures reliable and traceable automation workflows. |

### The 4 Core Agents

| Agent | What It Actually Does |
|-------|----------------------|
| **Planner** | Breaks down complex tasks into actionable steps, assigns subtasks to other agents, monitors progress. |
| **Coder** | Writes, reviews, and refactors code. Supports Python, JavaScript, TypeScript, Go, Rust, and more. |
| **SysAdmin** | Manages Docker containers, executes shell commands, monitors system health, handles deployments. |
| **Researcher** | Deep research across web and documents. Builds knowledge graphs, summarizes findings, cites sources. |

```bash
# Create a complex task
grace task "Build a FastAPI app with user auth, Docker container, and deploy to local K8s"

# Check agent status
grace agents status

# View task progress
grace tasks list
```

---

## Grace Cloud: Distributed & Scalable AI

Run your AI team across multiple machines for true parallel processing and scale.

| Component | Description | Advantage |
|-----------|-------------|-----------|
| **Distributed Workers** | Deploy worker nodes (Grace Workers) on different hardware, including GPU machines or home servers. | Scales AI computation horizontally for faster task completion. |
| **Message Bus** | Agents and workers communicate securely using structured messages (via Redis or NATS). | Enables robust, distributed multi-agent collaboration without centralized failure points. |
| **Kubernetes Ready** | Architecture is designed for deployment into Kubernetes or cloud environments. | Ready for production-level, high-availability AI infrastructure. |

---

## Grace Plugins: The Autonomous Ecosystem

Extend the capabilities of your AI OS with a powerful, developer-friendly plugin system.

| Plugin Type | Example Tools | Functionality |
|-------------|---------------|---------------|
| **DevOps** | Docker Tool, Kubernetes Tool, AWS Tool | Build, deploy, scale, and manage containerized applications autonomously. |
| **Coding** | Python Runner, Git Tool, Code Linter | Write code, run tests, commit changes, and fix bugs automatically. |
| **Research** | Web Search Tool, API Call Tool | Browse the internet, scrape data, and interact with external services for research tasks. |
| **System** | Filesystem Tool, Shell Tool, DB Tool | Organize files, manage cron jobs, query databases, and execute local scripts. |

---

## Security & Isolation: Built on Trust

Security is the core principle. Every AI action is treated as potentially dangerous and is isolated by default.

| Security Feature | Mechanism | Protection |
|-----------------|-----------|------------|
| **Docker Sandbox** | All shell and code execution runs inside isolated, disposable Docker containers. | Prevents `rm -rf /` or malicious code from harming the host machine. |
| **Permission Gating** | Critical actions (deleting files, deploying services) require explicit human approval via the Web UI. | Prevents accidental or LLM-hallucinated destructive commands. |
| **Secret Vault** | API keys, database passwords, and environment variables are stored in an isolated vault, shielded from the LLM. | Protects sensitive credentials from being leaked during AI reasoning. |
| **Tool Allowlisting** | Only approved and verified tools/commands are allowed to be executed by the agents. | Enforces a strict boundary on the AI's delegated authority. |

---

## Open Grace vs The Landscape

### Architecture Comparison

| Feature | Open Grace | OpenFang | AutoGen | CrewAI |
|---------|------------|----------|---------|--------|
| **Language** | Python | Rust | Python | Python |
| **Local LLM First** | ✅ Native Ollama | ✅ Native | ❌ Cloud-first | ❌ Cloud-first |
| **Docker Sandbox** | ✅ Built-in | ✅ Built-in | ❌ Manual | ❌ Manual |
| **Multi-Agent** | ✅ 4 Core Agents | ✅ 7 Hands | ✅ | ✅ |
| **Web UI** | ✅ React Dashboard | ✅ | ❌ CLI only | ❌ CLI only |
| **Mobile Support** | ✅ PWA | ❌ | ❌ | ❌ |
| **Plugin System** | ✅ SDK + Marketplace | ✅ FangHub | ❌ | ❌ |
| **Secret Vault** | ✅ AES-256 | ✅ | ❌ | ❌ |

---

## Open Grace Developer SDK

Build the next generation of autonomous agents and tools.

The Grace SDK makes it easy to integrate custom models, create specialized agents, and publish new tools to the community marketplace.

```python
# Example Agent Creation
from grace_sdk import GraceAgent, Tool

class CodeReviewer(GraceAgent):
    def plan(self, diff):
        # Uses Ollama for reasoning
        return self.model.review(diff)
    
    def execute(self, task):
        # Secure execution
        return self.run_tool('git', task)
```

| SDK Component | Purpose |
|---------------|---------|
| **Agent Base Class** | Provides a standard interface for creating new, specialized agents. |
| **Tool Definition** | Simple Python class structure to define new, executable tools. |
| **Model Connector** | API for routing tasks to specific local models (llama3, deepseek). |
| **Message Bus API** | Allows custom agents to communicate with the kernel and other agents. |

---

## Quick Start

### Requirements
- Python 3.10+
- Docker
- Ollama

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/opengrace-ii/open-grace
cd open-grace

# 2. Install dependencies
pip install -e .

# 3. Initialize Open Grace
grace init

# 4. Start the API server
uvicorn open_grace.api.server:app --reload

# 5. Start the frontend (new terminal)
cd frontend
npm install
npm run dev

# 6. Open http://localhost:5173
```

### Run Your First Agent

```bash
# CLI
grace run "Create a new FastAPI project and add a README"

# Or use the Web UI
# Navigate to http://localhost:5173 and chat with your AI team
```

---

## Project Structure

```
open-grace/
├── open_grace/
│   ├── agents/           # Core AI agents (Planner, Coder, SysAdmin, Researcher)
│   ├── api/              # FastAPI REST API & WebSocket endpoints
│   ├── cli/              # Command-line interface
│   ├── kernel/           # Task orchestration & scheduling
│   ├── memory/           # RAG engine, vector store, document processing
│   ├── model_router/     # LLM routing (Ollama, OpenAI, etc.)
│   ├── plugins/          # Plugin system & SDK
│   ├── sandbox/          # Docker sandbox for secure execution
│   ├── security/         # Auth, vault, permissions
│   └── taskforge/        # TaskForge engine core
├── frontend/             # React + TypeScript dashboard
├── tests/                # Test suite
└── docs/                 # Documentation
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Community

- [GitHub Discussions](https://github.com/opengrace-ii/open-grace/discussions)
- [Issues](https://github.com/opengrace-ii/open-grace/issues)
- [Twitter/X](https://twitter.com/opengrace_ai)

---

**Open Grace: Autonomous, Private, Powerful.**

Built with ❤️ by the Open Grace team.
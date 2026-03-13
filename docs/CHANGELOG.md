# Changelog

All notable changes to Open Grace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Advanced skill/plugin marketplace prototype
- Visual flow editor for agent workflows

## [1.1.0-alpha] - 2026-03-13

### Added
- **Evaluator Agent**: New specialized agent for plan validation and verification.
- **Bwrap Sandbox**: Secure, lightweight containerization using `bubblewrap` for non-Docker environments.
- **Modular Memory Architecture**: Separated `KnowledgeStore`, `ShortTermMemory`, and `LongTermMemory` for improved RAG and context management.
- **System Diagnostics**: Added `EventLogger` and `SystemGuard` for real-time monitoring and stability.
- **Task Queue & Scheduler**: Enhanced core orchestration for sequential task processing.

### Changed
- Refactored `SysAdminAgent` to support multiple sandbox backends (Docker/Bwrap).
- Improved `ModelRouter` with task-specific model selection.

### Fixed
- Stabilized agent execution loop during complex multi-step tasks.
- Improved error handling in the plugin system.

## [1.0.0] - 2026-03-10

### Added
- Initial release of Open Grace TaskForge AI
- **TaskForge Engine**: Core AI agent orchestration system
  - 4 specialized agents: Planner, Coder, SysAdmin, Researcher
  - Multi-agent collaboration and task delegation
  - Structured planning with task graphs
- **Grace Cloud**: Distributed AI infrastructure
  - Worker node support
  - Message bus for agent communication
  - Kubernetes-ready architecture
- **Grace Plugins**: Extensible plugin system
  - DevOps tools (Docker, K8s, AWS)
  - Coding tools (Python, Git, Linter)
  - Research tools (Web Search, API)
  - System tools (Filesystem, Shell, DB)
- **Security & Isolation**
  - Docker sandbox for all code execution
  - Permission gating for critical actions
  - AES-256 encrypted secret vault
  - Tool allowlisting
  - JWT authentication with device tracking
- **Memory & RAG**
  - Vector store with FAISS/ChromaDB
  - Document processing (PDF, DOCX, TXT, MD)
  - Knowledge graph construction
  - SQLite metadata store
- **Model Router**
  - Ollama integration for local LLMs
  - Support for llama3, mistral, deepseek
  - Hybrid routing (local + cloud)
- **Web Dashboard**
  - React + TypeScript frontend
  - Real-time task monitoring
  - Agent status visualization
  - Mobile-responsive design
  - PWA support
- **CLI Interface**
  - Task management commands
  - Agent control
  - Knowledge base management
  - Configuration management
- **API Server**
  - FastAPI-based REST API
  - WebSocket support for real-time updates
  - CORS enabled for mobile access
  - Comprehensive endpoints
- **Testing**
  - Unit tests for core components
  - Integration tests
  - Security tests

### Security
- Docker sandbox prevents host system compromise
- Secret vault protects API keys from LLM access
- Permission gates prevent accidental destructive actions
- Tool allowlisting enforces execution boundaries

## [0.9.0] - 2026-02-15

### Added
- Beta release for internal testing
- Basic agent swarm implementation
- Initial RAG pipeline
- Web UI prototype

### Changed
- Refactored task execution engine
- Improved agent communication protocol

### Fixed
- Memory leaks in long-running agents
- Race conditions in task scheduling

## [0.8.0] - 2026-01-20

### Added
- Alpha release
- Core orchestrator implementation
- Basic CLI interface
- Docker sandbox prototype

---

## Release Notes Template

```
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```
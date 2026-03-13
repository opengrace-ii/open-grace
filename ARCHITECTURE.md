# Open Grace Architecture

Open Grace is an autonomous AI operating system designed for multi-agent reasoning, self-improvement, and intelligent task execution.

## System Overview

The system consists of three main layers:

1.  **Backend (AI Runtime)**: The core engine that manages agents, memory, and task execution.
2.  **Dashboard (UI Control Center)**: A Next.js-based web interface for monitoring and interacting with the system.
3.  **Plugin Ecosystem**: A modular system for extending the capabilities of the agents.

## Subsystems

### 1. Agent Swarm
A collection of specialized agents (Planner, Researcher, Coder, Sysadmin, Evaluator) that work together to solve complex tasks.

### 2. Memory System
Provides short-term (contextual) and long-term (knowledge-based) storage for agents.

### 3. Orchestrator
The central component that coordinates agents, manages the task queue, and ensures secure execution in a sandbox environment.

### 4. Knowledge Store
A vector-based index for efficient retrieval of information.

## Technology Stack

- **Backend**: Python, FastAPI, asyncio.
- **Frontend**: Next.js, React, Tailwind CSS.
- **Database**: SQLite (for metadata), Vector Database (for embeddings).
- **Communication**: WebSockets for real-time updates.

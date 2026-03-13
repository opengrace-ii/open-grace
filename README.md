<p align="center">
  <img src="OG_Matelic.png" alt="Open Grace Logo" width="300">
</p>

# Open Grace

Open Grace is an autonomous AI operating system designed for multi-agent reasoning, self-improvement, and intelligent task execution.

## Features

- **Autonomous Agent Swarm**: Specialized agents working together for planning, research, coding, and evaluation.
- **Self-Improving Evaluation Loop**: Continuous feedback and improvement for task performance.
- **Plugin Ecosystem**: Easily extensible through a modular plugin architecture.
- **Secure Sandbox Execution**: Isolated environments for safe command and script execution.
- **Memory-Based Learning**: Integrated short-term and long-term memory for contextual awareness.
- **Hybrid Local/Cloud Models**: Support for local models (Ollama) and cloud providers (OpenAI, Anthropic, Gemini).
- **Real-Time Dashboard**: Comprehensive UI for monitoring system status and agent activities.

## Architecture

The swarm operates in a collaborative loop:
**Planner** → **Researcher** → **Coder** → **Sysadmin** → **Evaluator**

For more details, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Getting Started

### Installation
```bash
./scripts/setup.sh
```

### Running the Platform
```bash
docker-compose up
```

## Repository Structure

- `backend/`: AI runtime and agent logic.
- `dashboard/`: Next.js-based control center.
- `plugins/`: Extension ecosystem and marketplace.
- `docker/`: Deployment configurations.
- `tests/`: Reliability and simulation tests.
- `docs/`: Comprehensive documentation.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache 2.0 and MIT Licenses.
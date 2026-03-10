# Contributing to Open Grace

Thank you for your interest in contributing to Open Grace! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project and everyone participating in it is governed by our commitment to:
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Prioritize user safety and privacy

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please:
1. Check the [existing issues](https://github.com/opengrace-ii/open-grace/issues) to avoid duplicates
2. Use the latest version to verify the bug still exists
3. Collect information about the bug (logs, screenshots, environment)

When submitting a bug report, include:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Open Grace version)
- Any relevant logs or screenshots

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating one:
- Use a clear, descriptive title
- Provide a detailed description of the proposed feature
- Explain why this enhancement would be useful
- List any alternative solutions you've considered

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

#### Pull Request Guidelines

- Update documentation for any changed functionality
- Add tests for new features
- Ensure all tests pass
- Follow the existing code style
- Keep commits atomic and well-described

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Docker
- Ollama

### Backend Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/open-grace.git
cd open-grace

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Running the Full Stack

```bash
# Terminal 1: API Server
uvicorn open_grace.api.server:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Access at http://localhost:5173
```

## Project Structure

```
open-grace/
├── open_grace/          # Core Python package
│   ├── agents/          # AI agents
│   ├── api/             # REST API
│   ├── cli/             # Command line interface
│   ├── kernel/          # Task orchestration
│   ├── memory/          # RAG and vector store
│   ├── security/        # Auth and vault
│   └── taskforge/       # TaskForge engine
├── frontend/            # React dashboard
├── tests/               # Test suite
└── docs/                # Documentation
```

## Coding Standards

### Python
- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Maximum line length: 100 characters

### TypeScript/React
- Use functional components
- Follow the existing component structure
- Use TypeScript strictly
- Prefer `const` over `let`

### Testing
- Write unit tests for new functionality
- Aim for >80% code coverage
- Use pytest for Python, Vitest for TypeScript

## Plugin Development

Want to create a plugin? See our [Plugin SDK Guide](docs/plugin-development.md).

## Questions?

- Join our [GitHub Discussions](https://github.com/opengrace-ii/open-grace/discussions)
- Open an issue with the `question` label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
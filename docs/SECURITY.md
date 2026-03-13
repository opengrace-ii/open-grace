# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### Please DO NOT:
- Open a public issue describing the vulnerability
- Discuss the vulnerability in public forums
- Share exploit details publicly

### Please DO:
- Email security concerns to: **security@opengrace.io**
- Include detailed description of the vulnerability
- Provide steps to reproduce (if possible)
- Allow time for us to address the issue before public disclosure

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Fix Development**: Based on severity (typically 7-30 days)
- **Public Disclosure**: After fix is released and users have time to update

## Security Features

Open Grace implements multiple security layers:

### Docker Sandbox
All code execution runs in isolated, disposable containers.

### Permission Gating
Critical actions require explicit human approval.

### Secret Vault
AES-256 encrypted storage for API keys and credentials.

### Tool Allowlisting
Only approved tools can be executed by agents.

### JWT Authentication
Secure token-based authentication with device tracking.

## Security Best Practices

When using Open Grace:

1. **Keep Ollama Updated**: Regularly update your local LLM runner
2. **Review Agent Actions**: Monitor what agents are doing
3. **Use Docker**: Never disable the Docker sandbox in production
4. **Secure Your Vault**: Use strong master passwords
5. **Limit Network Access**: Run behind a firewall when possible
6. **Regular Updates**: Keep Open Grace updated to latest version

## Known Security Considerations

### LLM Prompt Injection
While we implement guardrails, LLMs can be manipulated. Always review agent outputs before approving critical actions.

### Local Execution
Open Grace runs locally, which means:
- ✅ Your data stays private
- ⚠️ You're responsible for system security

### Plugin Security
Third-party plugins run with the same permissions as built-in tools. Only install plugins from trusted sources.

## Security Changelog

### v1.0.0
- Initial security framework
- Docker sandbox implementation
- Secret vault with AES-256 encryption
- JWT authentication system
- Tool allowlisting

---

Thank you for helping keep Open Grace secure!
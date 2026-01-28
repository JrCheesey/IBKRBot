# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

IBKRBot handles connections to Interactive Brokers and sensitive trading data. We take security seriously.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of these methods:

1. **GitHub Private Vulnerability Reporting**: Use the "Report a vulnerability" button in the Security tab
2. **Email**: Create a private gist with details and share the link via GitHub Discussions (mark as private)

### What to Include

- Type of vulnerability (e.g., credential exposure, injection, authentication bypass)
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

### Security Best Practices for Users

1. **Never commit credentials**: Don't add API keys or passwords to config files in version control
2. **Use Paper Trading**: Test all strategies in paper trading mode first
3. **Firewall TWS/Gateway**: Only allow localhost connections to TWS/IB Gateway
4. **Keep Updated**: Always use the latest version of IBKRBot
5. **Review Orders**: Always verify bracket orders before confirming

## Scope

The following are in scope for security reports:

- Authentication/authorization issues
- Data exposure vulnerabilities
- Injection vulnerabilities
- Insecure data storage
- Issues that could lead to unintended trades

## Out of Scope

- Issues in third-party dependencies (report to those projects directly)
- Issues requiring physical access to the user's machine
- Social engineering attacks
- Denial of service attacks

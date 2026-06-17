# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| v1.4.x  | ✅ Yes    |
| v1.3.x  | ⚠️ Security fixes only |
| < v1.3  | ❌ No     |

## Reporting a Vulnerability

If you discover a security vulnerability in Linux Tweaker, please report it responsibly.

### How to Report

**Do NOT** open a public issue.

Instead, send an email to: [security@example.com](mailto:security@example.com)

Include the following information:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

### What to Expect

- We will acknowledge receipt within 48 hours
- We will provide a detailed response within 7 days
- We will work with you to understand and fix the issue
- Once fixed, we will announce the security update

### Security Best Practices

Linux Tweaker is designed to run without root privileges. However, users should:

1. **Review the install script** before running:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/xxxxpeterxxxxxx-cloud/linux-tweaker/main/install.sh | less
   ```

2. **Use the official repository** only:
   - GitHub: https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker
   - Avoid third-party mirrors

3. **Check the checksum** (future feature):
   ```bash
   sha256sum linux-tweaker.tar.gz
   ```

4. **Run with user privileges only** — the tool never requires root

### Known Security Considerations

- **Theme downloads**: Themes are downloaded from external GitHub repositories. Review preset JSON files before applying.
- **Install scripts**: Some themes run install scripts. These are executed with user privileges only.
- **Config modifications**: The tool modifies `~/.config/` files. Backups are created automatically.

### Dependency Security

We regularly update dependencies. Report any vulnerable dependencies via the security email above.

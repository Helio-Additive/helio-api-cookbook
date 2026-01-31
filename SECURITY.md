# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
responsibly by emailing the maintainers directly rather than opening a public
issue.

## PAT Token Security

- Never commit your PAT token to version control
- Use environment variables (`HELIO_PAT`) or the config file (`~/.helio_config`)
- The `.gitignore` excludes `.env` files to prevent accidental commits
- Tokens are only sent to the Helio API endpoint over HTTPS

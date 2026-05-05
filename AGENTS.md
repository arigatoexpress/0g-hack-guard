# 0guard — Agent Guide

## Project Overview

0guard is a **0G-native agent guard** with signature & behavioral detection for crypto hacks. It monitors blockchain transactions, social media (X/Twitter, Telegram), and on-chain activity to detect and alert on potential security threats.

**Key capabilities:**
- Signature-based detection of known exploit patterns
- Behavioral anomaly detection for suspicious transactions
- Social media monitoring for hack announcements and scam alerts
- Policy engine for customizable security rules
- Content generation for security awareness posts

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Blockchain     │────▶│  0guard Engine   │────▶│  Alert Channels │
│  (0G, EVM)      │     │  (detection)     │     │  (Telegram, X)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│  Signature DB   │     │  Policy Engine   │
│  (known hacks)  │     │  (custom rules)  │
└─────────────────┘     └──────────────────┘
```

**Core modules:**
- `crypto_hack_guard.py` — Signature & behavioral detection engine
- `policy.py` — Configurable security policies and rules
- `app.py` — Flask web server with health checks and API
- `x_bot.py` — X/Twitter bot for monitoring and posting
- `telegram_bot.py` — Telegram bot for alerts and commands
- `content_engine.py` — Security content generation
- `storage.py` — Data persistence layer
- `cli.py` — Command-line interface

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| Runtime | Flask 3.0+ |
| Blockchain | web3 7.0+, eth-utils 5.0+ |
| Social | tweepy 4.14+ |
| Testing | pytest 8.0+, pytest-cov 5.0+ |
| Linting | ruff 0.6+ |
| Containerization | Docker |

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest -q

# Run tests with coverage
pytest -q --cov=src/guard0 --cov-report=html

# Run linting
ruff check src tests scripts

# Run the Flask app
python -m guard0.app

# Run the CLI
0guard --help

# Build Docker image
docker build -t 0guard .

# Run Docker container
docker run -p 8109:8109 0guard
```

## CI/CD

GitHub Actions workflows:
- **test** — Lint (ruff), test with coverage (pytest-cov, 60% gate), compile check, demo smoke test
- **docker** — Docker build + health check (main branch only)

## Safety Boundaries (MUST NOT CHANGE)

1. **No private key exposure** — Never log, store, or transmit private keys or mnemonics.
2. **No unauthorized transactions** — The detection engine must never sign or broadcast transactions.
3. **No social media spam** — Bots must respect rate limits and never post without policy approval.
4. **Testnet-first** — Blockchain interactions default to testnet unless explicitly configured for mainnet.

## Agent Conventions

- Use **type hints** where practical.
- Run **ruff** before committing (`ruff check src tests scripts`).
- Write **tests** for new detection signatures and policies.
- Use **conventional commits**: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Update `AGENTS.md` if you change the architecture or safety boundaries.

## Deployment

### Docker
```bash
docker build -t 0guard .
docker run -d -p 8109:8109 --env-file .env 0guard
```

### Render (planned)
Connect repo to Render Dashboard and use Docker deployment.

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `PORT` | Flask server port | No (default 8109) |
| `X_API_KEY` / `X_API_SECRET` | X/Twitter API credentials | For X bot |
| `X_ACCESS_TOKEN` / `X_ACCESS_SECRET` | X/Twitter user credentials | For X bot |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token | For Telegram bot |
| `TELEGRAM_CHAT_ID` | Default Telegram chat for alerts | For Telegram bot |
| `WEB3_PROVIDER_URI` | Blockchain RPC endpoint | For on-chain detection |

## Contributing

1. Create a feature branch: `git checkout -b feat/description`
2. Make changes with tests
3. Run the full check suite: `pytest -q && ruff check src tests scripts`
4. Open a PR against `main`

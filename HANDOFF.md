# 0guard — Handoff Checklist

> Everything built. Everything documented. Here's what you need to do.

---

## ✅ What We Built (Complete)

| Component | Status | Lines/Tests |
|-----------|--------|-------------|
| **Core Engine** | ✅ | `guard0` package, 100 tests passing |
| **Hack Signatures** | ✅ | 60+ incidents (2020-2026), 10 attack vectors, 29 IOCs, 32 selectors |
| **0G Chain** | ✅ | Live Galileo status endpoint, `PolicyReceiptAnchor.sol`, deployment scripts ready |
| **0G Storage** | ✅ | Threat-intel payload/root-hash preparation; external writes opt-in |
| **OSINT Pipeline** | ✅ | Source registry, live public metadata signals, source readiness, signature gap map |
| **Content Engine** | ✅ | Generates tweets/threads/summaries from incident data |
| **X Bot** | ✅ | Posts via explicit confirmation workflow; no surprise sends |
| **Landing Page** | ✅ | GitHub Pages live, self-contained, animated, responsive |
| **Flask API + Dashboard** | ✅ | `/api/evaluate`, `/api/hack-check`, `/api/0g/status`, `/api/0g/receipt`, `/api/osint/*`, `/api/hackathon/submission-brief` |
| **CLI** | ✅ | `0guard evaluate`, `hack-check`, `health`, `serve` |
| **Docker** | ✅ | Dockerfile + docker-compose.yml |
| **CI/CD** | ✅ | GitHub Actions (test, lint, browser smoke, Docker health, Pages deploy, confirmed X workflow) |
| **Demo Script** | ✅ | `scripts/demo_april_2026.py` |
| **Deployment Guide** | ✅ | `DEPLOYMENT.md` |
| **Video Script** | ✅ | `docs/DEMO_VIDEO_SCRIPT.md` |
| **Pitch Deck** | ✅ | 12 slides with speaker notes |
| **X Thread Copy** | ✅ | 5-tweet thread ready to post |

**Repo:** https://github.com/arigatoexpress/0guard
**Live landing page:** https://arigatoexpress.github.io/0guard/

---

## 🔴 What I Need From You (Action Items)

### 1. Deploy the Smart Contract on 0G Testnet
**Why:** Required for 0G integration proof in hackathon submission.

```bash
cd /Users/aribs/Code/0guard

# Step 1: Get testnet funds
# Go to https://faucet.0g.ai
# Paste your wallet address, get 0.1 0G/day

# Step 2: Export your private key
export PRIVATE_KEY=0x...

# Step 3: Deploy
.venv/bin/python scripts/deploy_0g.py --network testnet

# Step 4: Copy the contract address from output
export ZGG_RECEIPT_CONTRACT=0x...

# Step 5: Update .env
cat >> .env << EOF
ZGG_CHAIN_RPC=https://evmrpc-testnet.0g.ai
ZGG_CHAIN_ID=16602
ZGG_RECEIPT_CONTRACT=$ZGG_RECEIPT_CONTRACT
EOF
```

**Time:** 15 minutes  
**Blockers:** Need 0G testnet funds (faucet.0g.ai)

---

### 2. Get X API Credentials
**Why:** Required to post the hackathon thread and run the X bot.

1. Go to https://developer.x.com/en/portal/dashboard
2. Apply for Elevated access (if not already approved)
3. Create a Project → Create an App
4. Enable **"User authentication settings"** → **"Read and Write"**
5. Go to **"Keys and Tokens"**:
   - API Key → `X_CONSUMER_KEY`
   - API Secret → `X_CONSUMER_SECRET`
   - Access Token → `X_ACCESS_TOKEN`
   - Access Token Secret → `X_ACCESS_TOKEN_SECRET`
6. Add to `.env`:

```bash
cat >> .env << EOF
X_CONSUMER_KEY=...
X_CONSUMER_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
EOF
```

**Time:** 10 minutes  
**Blockers:** Need X Developer account approval (can take 1-2 days if new)

---

### 3. Post the Hackathon X Thread
**Why:** Required by hackathon submission rules.

```bash
cd /Users/aribs/Code/0guard
source .venv/bin/activate

# Dry run first
python scripts/x_post.py --file content/hack_guard_thread.json --thread --dry-run

# If it looks good, post live
python scripts/x_post.py \
  --file content/hack_guard_thread.json \
  --thread \
  --live-post-confirm POST_TO_X_FROM_0GUARD
```

**Copy is already written.** See `content/hack_guard_thread.json`.

**Time:** 5 minutes  
**Blockers:** Needs X API credentials (see #2)

---

### 4. Review the OSINT/Submission Brief
**Why:** This is now the fastest way to inspect the data-product and HackQuest
submission posture.

```bash
cd /Users/aribs/Code/0guard
source .venv/bin/activate
python -m guard0.app

curl -s http://127.0.0.1:8109/api/hackathon/submission-brief | python -m json.tool
curl -s http://127.0.0.1:8109/api/data/signature-map | python -m json.tool
curl -s 'http://127.0.0.1:8109/api/osint/signals?live=1&limit=10' | python -m json.tool
```

**What it proves:** source-rights metadata, live OSINT leads, detector gaps,
data stats, 0G story, and the manual operator TODO list.

---

### 5. Record the Demo Video (≤3 min)
**Why:** Required by hackathon submission. Slide-only videos are REJECTED.

Follow `docs/DEMO_VIDEO_SCRIPT.md` step-by-step:

1. **Setup:**
   - Open 3 terminal tabs
   - Tab 1: `python3 -m guard0.app` (Flask server)
   - Tab 2: `python3 scripts/demo_april_2026.py` (CLI demo)
   - Tab 3: Browser at `http://127.0.0.1:8109` (dashboard)

2. **Record with OBS Studio** (free):
   - 1080p canvas, x264, 8000 Kbps
   - Follow timestamps 0:00-3:00 in script

3. **Upload to YouTube** (unlisted or public)

**Time:** 2-3 hours  
**Blockers:** None — script has fallback plans for crashes

---

### 6. Verify GitHub Pages
**Why:** The landing page is already live at `https://arigatoexpress.github.io/0guard/`.

```bash
curl -I https://arigatoexpress.github.io/0guard/
```

The workflow `.github/workflows/pages.yml` auto-deploys on every push that changes `docs/**`.

**Time:** 30 seconds
**Blockers:** None

---

### 7. Submit to HackQuest
**Why:** The actual hackathon submission.

Go to https://hackquest.io/en/hackathons/0G-APAC-Hackathon

**You need:**
- [ ] Project name: `0guard`
- [ ] One-sentence description (copy from README)
- [ ] GitHub repo link: `https://github.com/arigatoexpress/0guard`
- [ ] 0G contract address + explorer link. Current HackQuest wording asks for
      mainnet proof; use mainnet only if you intentionally fund/deploy it.
      Otherwise submit Galileo proof and state the mainnet gap clearly.
- [ ] Demo video URL (YouTube)
- [ ] README with architecture diagram
- [ ] X post URL (with `#0GHackathon #BuildOn0G`)
- [ ] Team info

**Time:** 30 minutes  
**Blockers:** Needs #1 (contract deploy) and #4 (video)

---

## 🟡 Nice-to-Have (Post-Submission)

| Task | Effort | Impact |
|------|--------|--------|
| Deploy contract on **0G mainnet** | 15 min | Higher credibility |
| Set up **GitHub Secrets** for X workflow | 5 min | Enables explicit confirmed posts for new signatures |
| Add **og-image.png** to docs/ | 30 min | Better social sharing |
| Create a **pitch deck PDF** | 1-2 hrs | If judges request it |
| Add **more historical incidents** to data/ | Ongoing | Better detection |

---

## 🚀 Quick Commands Reference

```bash
cd /Users/aribs/Code/0guard

# Run tests
make test

# Run demo
make demo

# Start server
make run

# Generate content
make content

# Dry-run X post
make x-post

# Deploy contract
make deploy

# Docker
make docker-build
make docker-run

# Lint + format
make lint
make fmt
```

---

## 📞 If Something Breaks

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'guard0'` | Run `.venv/bin/python -m pip install -e '.[dev]'` |
| Tests fail after rename | Delete `.venv` and recreate: `python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'` |
| X bot 403 error | Regenerate Access Token in X Developer Portal |
| Contract deploy fails | Check balance: `curl -X POST https://evmrpc-testnet.0g.ai -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["YOUR_ADDRESS","latest"],"id":1}'` |

---

## 🎯 Bottom Line

**Submission is due May 16, 2026 at 23:59 UTC+8 / 09:59 MDT.**

The code is done. The docs are done. The tests pass. The landing page is live.
The OSINT/source-readiness and submission-brief surfaces are now in the app.

**Your only real blockers are:**
1. Get 0G funds for the chosen network → deploy contract (15 min)
2. Record video (2-3 hrs)
3. Post required X thread (5 min after credentials)
4. Submit form (30 min)

Everything else is ready to copy-paste.

---

*Built by Sapphire Security + arigatoexpress for the 0G APAC Hackathon 2026.*

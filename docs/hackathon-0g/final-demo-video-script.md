# 0guard Final Demo Video Script

Final generated length: 2:01.1.

Submission rule: HackQuest requires a public demo video of no more than three
minutes that shows product functionality, user flow, and actual 0G component
usage. This cut is a real product walkthrough, not a slide deck.

Generated asset:

```text
https://arigatoexpress.github.io/0guard/hackathon-0g/assets/0guard-hackquest-demo-final.mp4
```

Rebuild command:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/build_hackquest_demo_video.py
```

## Core Story

0guard is a pre-wallet firewall for AI agents. In plain terms: an agent asks,
0guard checks, and the wallet stays protected. Safe read-only simulations can
continue. Risky live wallet actions are denied before the signer ever sees a
transaction.

The technical proof is shown after the simple explanation: real April 2026
incident data, deterministic receipt hashes, Storage-ready roots, a public 0G
mainnet receipt anchor, and source-aware provenance.

## Final Timeline

| Time | Narration | Visual |
| --- | --- | --- |
| 0:00-0:13 | "Imagine an AI agent is about to use your wallet. Before it can ask for a signature, 0guard checks what the agent is trying to do." | Open on the 0guard workbench story board with the agent, 0guard gate, wallet, and receipt nodes visible. |
| 0:13-0:21 | "The simple idea is this: agent request, 0guard check, then wallet. Safe simulations can continue. Risky live actions stop before signing." | Keep the visual flow in frame. The packet moves through the simple model. |
| 0:21-0:34 | "First, the agent is tricked into pre-signing an admin transfer. 0guard blocks the social-engineering ask before the wallet is involved." | Run the social-engineering scenario. Show the packet stopping at 0guard and the wallet reading `not asked to sign`. |
| 0:34-0:46 | "Next, the agent is asked to release bridge funds through a weak verifier setup. 0guard catches the bridge risk and denies it." | Run the bridge release scenario. Show the red blocker chips and deny verdict. |
| 0:46-0:58 | "Then, a compromised admin path tries to upgrade a contract. 0guard sees the upgrade sequence and stops the wallet step." | Run the upgrade scenario. Keep the visual deny path centered. |
| 0:58-1:08 | "Good requests still work. A read-only simulation does not move funds, does not need a signature, and can pass through safely." | Run the safe simulation scenario. Show the allow state and `simulation only` wallet label. |
| 1:08-1:20 | "Now the technical proof: the demo is grounded in real incident data, not mock claims. It tracks 28 April 2026 cases and 635.24 million dollars in reported losses." | Click `Load data summary`. Show the incident summary and source list. |
| 1:20-1:30 | "Every verdict becomes a receipt hash. The browser workbench remains safe: no private key, no signing, no transaction broadcast, and no money movement." | Show the 0G read-only status and safety flags. |
| 1:30-1:39 | "For this submission, one deny receipt is already anchored on 0G mainnet. The public explorer proves that the receipt anchor exists." | Show the PolicyReceiptAnchor proof data from `docs/hackathon-0g/mainnet-proof.json`. |
| 1:39-1:49 | "0guard also prepares Storage-ready receipt roots and a provenance matrix. Judges can see source-aware evidence and hashes, without raw payload resale." | Show provenance coverage, source matches, and raw-payload safety. |
| 1:49-1:55 | "Autonomous finance needs more than smart agents. It needs simple pre-wallet protection, technical proof, and provenance. That is 0guard, built on 0G." | End on the cross-chain/read-only guardrail surface and final 0guard caption. |

## Exact Demo Scenarios

The reproducible builder calls the browser-only story runner for four scenarios:

```text
drift   - durable-nonce social-engineering admin transfer
bridge  - LayerZero-style bridge release with weak verifier risk
upgrade - proxy upgrade request from a compromised admin path
safe    - read-only simulation using eth_call with no signature
```

It then drives the real workbench controls for:

```text
/api/data/summary
/api/0g/status
/api/evaluate with enable_0g_anchor and enable_0g_storage
docs/hackathon-0g/mainnet-proof.json readback
/api/data/provenance
/api/integrations/cross-chain
```

Mainnet proof links:

```text
docs/hackathon-0g/mainnet-proof.json
https://chainscan.0g.ai/address/0xBaC59b1571b7c7195915c5B36D8A719Ed7182abc
https://chainscan.0g.ai/tx/64ff260ccd02aa69fc18d5727eb4530d8774003bc7df63ec7d5cda036fc438ed
```

## Audio Notes

The builder prefers a neural `edge-tts` voice when available, then falls back to
macOS `say`. It also accepts a finished voiceover through
`DEMO_NARRATION_AUDIO=/path/to/voiceover.wav`, which lets a manually recorded or
OpenAI/ElevenLabs export replace the generated narration without changing the
screen recording.

Current default local voice settings:

```text
DEMO_TTS_ENGINE=auto
DEMO_EDGE_TTS_VOICE=en-US-AndrewMultilingualNeural
DEMO_EDGE_TTS_RATE=+8%
DEMO_EDGE_TTS_PITCH=+0Hz
```

The final audio path still uses segmented narration, short controlled pauses,
high-pass and low-pass filtering, compression, light presence EQ, loudness
normalization, and fade-in/fade-out padding. This avoids the old abrupt stop and
reduces the strange pauses from one large text-to-speech paragraph.

Objective checks from the final MP4:

```text
video: 1920x1080, 25 fps, 121.12 seconds
audio: AAC mono, 117.71 seconds, mean volume -17.0 dB, max volume -1.5 dB
silence check: no internal >1.0 second silence detected at -35 dB threshold
```

## Safety Notes

- The demo performs no signing, transaction broadcast, bridge, swap, LIT order,
  Telegram send, or X post from the browser.
- 0G status is read-only.
- The anchored receipt is shown as public proof; the workbench remains
  simulation-first and explicit-confirmation-only for any live external action.

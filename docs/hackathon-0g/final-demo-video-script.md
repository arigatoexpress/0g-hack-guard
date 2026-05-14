# 0guard Final Demo Video Script

Final generated length: 2:18.0.

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
mainnet receipt anchor, source-aware provenance, and the current signature map.

## Final Timeline

| Time | Narration | Visual |
| --- | --- | --- |
| 0:00-0:13 | "Picture this: an AI agent is about to use your wallet. Before the wallet ever opens, 0guard reads the intent and asks whether this is safe to put in front of a signer." | Open on the 0guard workbench story board with the agent, 0guard gate, wallet, and receipt nodes visible. |
| 0:13-0:21 | "The flow is simple: request, policy check, then wallet. Simulations can keep moving. Anything that moves funds, changes ownership, or asks for a live signature has to pass the guard first." | Keep the visual flow in frame. The packet moves through the simple model. |
| 0:21-0:34 | "Here, the agent is tricked into pre-signing an admin transfer. 0guard catches the social-engineering pattern before the wallet is even asked." | Run the social-engineering scenario. Show the packet stopping at 0guard and the wallet reading `not asked to sign`. |
| 0:34-0:46 | "Now the request changes: release bridge funds through a weak verifier setup. That is exactly the kind of cross-chain shortcut 0guard is built to stop." | Run the bridge release scenario. Show the red blocker chips and deny verdict. |
| 0:46-0:58 | "Then a compromised admin path tries to upgrade a contract. The system does not need to guess; it sees the risky sequence and blocks the wallet step." | Run the upgrade scenario. Keep the visual deny path centered. |
| 0:58-1:08 | "Good requests still work. A read-only simulation does not move funds, does not need a signature, and should be allowed to continue." | Run the safe simulation scenario. Show the allow state and `simulation only` wallet label. |
| 1:08-1:20 | "Now we move from plain English to proof. This is the April 2026 source-linked incident set: 28 cases, with about 635 million dollars in reported losses." | Click `Load data summary`. Show the incident summary and source list. |
| 1:20-1:30 | "Every verdict becomes a receipt hash. The browser workbench stays safe: no private key, no signing, no broadcast, and no money movement." | Show the 0G read-only status and safety flags. |
| 1:30-1:39 | "For this submission, one deny receipt is already anchored on 0G mainnet, so judges can verify that the proof is not just a local demo." | Show the PolicyReceiptAnchor proof data from `docs/hackathon-0g/mainnet-proof.json`. |
| 1:39-1:49 | "0guard also prepares Storage-ready roots and a provenance matrix. Every incident has source evidence and hashes, while raw upstream payloads stay out of resale." | Show provenance coverage, source matches, and raw-payload safety. |
| 1:49-1:59 | "The detector map is honest and measurable. It matches 27 of the 28 incident patterns, and leaves Quant in research mode until the public root-cause evidence is stronger." | Click `Load signature map`. Show `matchedCount=27`, `gapCount=1`, and `Quant` as the only unmatched row. |
| 1:59-2:08 | "For external systems, 0guard is a checkpoint, not a launch button. Base and Virtuals, paid API rails, Ethereum-compatible networks, Celestia, Lighter exchange intents, and bridge protocols all stay read-only here." | Show the read-only cross-chain catalog. |
| 2:08-2:20 | "Autonomous finance needs more than smart agents. It needs a clear checkpoint before the wallet, real technical proof, and provenance. That is 0guard, built on 0G." | End on the cross-chain/read-only guardrail surface and final 0guard caption. |

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
/api/data/signature-map
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
DEMO_EDGE_TTS_VOICE=en-US-BrianNeural
DEMO_EDGE_TTS_RATE=+2%
DEMO_EDGE_TTS_PITCH=+0Hz
```

The final audio path still uses segmented narration, short controlled pauses,
high-pass and low-pass filtering, compression, light presence EQ, loudness
normalization, and fade-in/fade-out padding. This avoids the old abrupt stop and
reduces the strange pauses from one large text-to-speech paragraph.

Objective checks from the final MP4 after rebuild:

```text
video: 1920x1080, 25 fps, 137.92 seconds
audio: AAC mono, 137.99 seconds, mean volume -16.2 dB, max volume -1.5 dB
silence check: no internal >1.0 second silence detected at -35 dB threshold
```

## Safety Notes

- The demo performs no signing, transaction broadcast, bridge, swap, Lighter
  order, LIT token/staking/fee-credit action, Telegram send, or X post from the
  browser.
- 0G status is read-only.
- The anchored receipt is shown as public proof; the workbench remains
  simulation-first and explicit-confirmation-only for any live external action.

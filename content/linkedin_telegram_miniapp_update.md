# LinkedIn Telegram Mini App Update Draft

0guard now has a live Telegram Mini App.

The new bot is here:
https://t.me/Raris0guardBot

The Mini App is here:
https://guard0-miniapp-s77j6bxyra-uc.a.run.app/telegram

What changed:

- 0guard now runs as a mobile Telegram Mini App surface.
- Telegram launch data is validated server-side before user identity is trusted.
- The Mini App returns a wallet-alert preview plus a Mira explanation.
- The safety boundary stays intact: no wallet signing, no transaction
  broadcasting, and no Telegram sends from the Mini App.
- The bot menu button opens the live 0guard Mini App directly.

This is a meaningful step for the project because it moves 0guard closer to the
place where people actually need help: the moment an autonomous agent is about
to ask a wallet for a signature.

The broader hackathon proof stack is still the same:

- 28/28 April 2026 incidents source-linked.
- 28/28 incident-derived patterns covered by deterministic detectors.
- A public 0G mainnet receipt anchor.
- Read-only wallet alert previews.
- Source-aware provenance instead of mock claims.
- Cross-chain guardrails for EVM, x402, Virtuals/Base, Lighter, CCIP,
  LayerZero, Wormhole, and Celestia proof lanes.

0guard is not trying to be another wallet scanner. The goal is earlier:
agent intent first, signer later.

#0GHackathon #BuildOn0G #AIagents #Web3Security #CryptoSecurity #TelegramMiniApp

# Native Preflight Strategy

`0guard` should not become a bridge, exchange bot, or wallet custodian. The
portable product is simpler and stronger: one preflight call before an agent,
wallet app, payment rail, dWallet, Telegram surface, or exchange context reaches
a signer.

## What Shipped

- `POST /api/native-preflight`
  - Runs the core 0guard policy engine.
  - Adds Ika/Ikavery/MPCKit/OdWS checks when a dWallet or Ika surface is in
    scope.
  - Adds external guardrail checks for x402, Virtuals/Base, Lighter, CCIP,
    LayerZero, Wormhole, Celestia, and Ika.
  - Adds TON passport posture when a TON surface or address is supplied.
  - Returns one `allow`, `review`, or `deny` decision and a 0G-ready receipt
    hash.

- `GET /api/hackathon/strategy`
  - Keeps the build order grounded in timing and fit.
  - Puts the submitted 0G APAC project first.
  - Frames Arbitrum and ETHGlobal as follow-on middleware targets.

## Product Thesis

0G remains the proof and provenance layer. Other chains and ecosystems should
enter through native read-only adapters, simulations, policy receipts, or
pre-signing checks. If the integration requires bridging, sweeping, trading,
settling, launching, or sending messages to prove value, it is probably the
wrong first integration path.

## Next Build Order

1. Keep the 0G APAC submission, mainnet receipt proof, CI, Pages, and Mini App
   health green through final review.
2. Add SDK examples that call `/api/native-preflight` before AgentKit, Turnkey,
   Safe, MPCKit, or OdWS signing.
3. Add the rights-aware reputation adapter before stronger alerting claims.
4. Revisit live 0G Storage and Compute only after credentials, rollback notes,
   and operator approval are ready.

## Safety Boundary

The native preflight API is read-only. It does not request wallet signatures,
does not import keys, does not create dWallets, does not sign messages, does not
broadcast transactions, does not bridge, does not settle x402, does not place
exchange orders, and does not send Telegram/X/LinkedIn messages.

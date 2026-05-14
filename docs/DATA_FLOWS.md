# 0guard Data Flows

## Goal

Turn the incident list into a validated, inspectable data product instead of
loose demo copy.

## Current Pipeline

1. Load `data/april_2026_incidents.json`.
2. Validate required fields:
   - `id`
   - `date`
   - `protocol`
   - `loss_usd`
   - `chain`
   - `attack_vector`
   - `description`
   - `attribution`
   - `lesson`
3. Check dataset invariants:
   - unique integer IDs
   - ISO dates
   - non-empty text fields
   - non-negative integer losses
   - meta incident count equals row count
   - meta total loss equals computed total
4. Compute a SHA-256 dataset fingerprint.
5. Produce summary statistics:
   - total and average loss
   - top losses
   - chain counts
   - attack-vector counts
   - attribution counts
6. Convert incidents into preview-mode detection seeds and run them through the
   signature engine.
7. Explain per-incident signature coverage, detector gaps, and recommended
   rule additions.
8. Maintain a rights-aware OSINT source registry with explicit source owner,
   retrieval mode, TTL, output policy, and caveats.
9. Optionally fetch live public metadata signals from enabled adapters without
   returning raw payload dumps.
10. Promote reviewed derived source evidence into per-incident provenance fields
   while leaving unresolved incidents explicitly aggregate-only.

## API Readbacks

| Route | Purpose |
|---|---|
| `/api/data/summary` | Validation, fingerprint, aggregate stats, top losses. |
| `/api/data/incidents` | Filterable public incident rows. |
| `/api/data/provenance` | Per-incident provenance matrix and optional live DeFiLlama correlation. |
| `/api/data/detection-coverage` | Signature-engine coverage over incident-derived seeds. |
| `/api/data/signature-map` | Per-incident match explanation, gaps, and recommended detectors. |
| `/api/osint/sources` | Rights-aware source registry and output policy. |
| `/api/osint/readiness` | Catalog posture; `?live=1` performs public availability checks. |
| `/api/osint/signals` | Normalized incident/research leads; `?live=1` fetches live public metadata. |
| `/api/hackathon/submission-brief` | HackQuest-ready brief, data stats, 0G story, and operator TODOs. |
| `/api/hackathon/submission-packet` | Copy-ready HackQuest form fields and explicit operator placeholders. |
| `/api/hackathon/readiness` | Final HackQuest readiness audit with mainnet proof, demo, and X blockers. |

Example:

```bash
curl -s http://127.0.0.1:8109/api/data/summary | python3 -m json.tool
curl -s 'http://127.0.0.1:8109/api/data/incidents?chain=Ethereum&min_loss_usd=100000&limit=5' | python3 -m json.tool
curl -s 'http://127.0.0.1:8109/api/data/provenance?live=1' | python3 -m json.tool
curl -s http://127.0.0.1:8109/api/data/detection-coverage | python3 -m json.tool
curl -s http://127.0.0.1:8109/api/data/signature-map | python3 -m json.tool
curl -s http://127.0.0.1:8109/api/osint/sources | python3 -m json.tool
curl -s 'http://127.0.0.1:8109/api/osint/signals?live=1&limit=10' | python3 -m json.tool
curl -s http://127.0.0.1:8109/api/hackathon/submission-packet | python3 -m json.tool
curl -s http://127.0.0.1:8109/api/hackathon/readiness | python3 -m json.tool
```

## Provenance

The dataset carries aggregate upstream source URLs in `meta.source_urls`.
It also now carries per-incident `source_urls` and `derived_source_evidence`
for 26 of 28 incidents promoted from the reviewed provenance cache. The two
remaining aggregate-only records are `Silo V2` and `Denaria Finance`; the
validator reports those as a warning rather than pretending the records are
fully sourced.

`data/osint_sources.json` is the source-rights registry for the next layer of
provenance. Each source records:

- source owner and URL
- retrieval mode and freshness TTL
- license or rights envelope
- output policy
- caveats and disabled/default status

Default outputs are derived metadata, links, hashes, readiness, and defensive
analysis. Raw upstream payloads are not exposed by API routes.

The provenance matrix uses `data/incident_provenance_cache.json` for a reviewed
derived-evidence cache, so the judge demo remains useful without network access.
It can also correlate canonical incidents against DeFiLlama's public hack index
when `?live=1` is supplied. Both modes return matched source metadata,
confidence, record hashes, and a recommended next step for each incident. This
keeps live source evidence separate from raw upstream payloads, while preserving
the reviewed derived evidence in `data/april_2026_incidents.json`.

Next durable upgrade:

- Add `evidence_type` per source, such as `postmortem`, `transaction`, `security_report`, or `news`.
- Add protocol postmortem or transaction-level source URLs for `Silo V2` and
  `Denaria Finance`.
- Add `detection_seed` overrides for cases where the generic attack vector is
  too weak to exercise the signature engine.
- Promote catalog-only sources with compatible licenses into normalized
  adapters one at a time.
- Store the normalized dataset fingerprint in 0G Storage once live storage
  credentials are configured.

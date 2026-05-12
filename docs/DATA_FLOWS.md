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

## API Readbacks

| Route | Purpose |
|---|---|
| `/api/data/summary` | Validation, fingerprint, aggregate stats, top losses. |
| `/api/data/incidents` | Filterable public incident rows. |
| `/api/data/detection-coverage` | Signature-engine coverage over incident-derived seeds. |

Example:

```bash
curl -s http://127.0.0.1:8109/api/data/summary | python3 -m json.tool
curl -s 'http://127.0.0.1:8109/api/data/incidents?chain=Ethereum&min_loss_usd=100000&limit=5' | python3 -m json.tool
curl -s http://127.0.0.1:8109/api/data/detection-coverage | python3 -m json.tool
```

## Provenance

The dataset now carries aggregate upstream source URLs in `meta.source_urls`.
Per-incident source URLs are still missing, and the validator reports that as a
warning rather than pretending the records are fully sourced.

Next durable upgrade:

- Add `source_urls` per incident.
- Add `evidence_type` per source, such as `postmortem`, `transaction`, `security_report`, or `news`.
- Add `confidence` per incident.
- Add `detection_seed` overrides for cases where the generic attack vector is
  too weak to exercise the signature engine.
- Store the normalized dataset fingerprint in 0G Storage once live storage
  credentials are configured.

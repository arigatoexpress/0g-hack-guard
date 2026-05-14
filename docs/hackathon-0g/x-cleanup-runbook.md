# X Media Cleanup Runbook

This is the safe path for Ari's request to remove non-submission X media after
the HackQuest project is submitted.

## Boundary

- Do not delete posts directly from browser memory, screenshots, or stale local
  assumptions.
- Keep the submitted HackQuest proof post by default:
  `https://x.com/rariwrldd/status/2054779961425461542`.
- Generate a manifest, review it, run a dry-run delete pass, then require fresh
  explicit confirmation for live deletion.

## Commands

Generate a template without X credentials:

```bash
.venv/bin/python scripts/x_media_cleanup.py --template --manifest-out content/x_media_cleanup_manifest.template.json
```

Generate a real review manifest from the authenticated account timeline:

```bash
.venv/bin/python scripts/x_media_cleanup.py --manifest-out content/x_media_cleanup_manifest.review.json
```

Dry-run deletion from the reviewed manifest:

```bash
.venv/bin/python scripts/x_media_cleanup.py --delete-from-manifest content/x_media_cleanup_manifest.review.json --dry-run
```

Live deletion, only after Ari reviews the manifest:

```bash
.venv/bin/python scripts/x_media_cleanup.py --delete-from-manifest content/x_media_cleanup_manifest.review.json --live-delete-confirm DELETE_X_MEDIA_FROM_0GUARD
```

## Review Rules

- `keep=true` means the post is preserved.
- `deleteRecommended=true` means the script will delete that post only if the
  live confirmation flag is supplied.
- Add any X post IDs that should survive with `--keep-tweet-id` or `--keep-url`
  when generating the manifest.
- Save the reviewed manifest next to the submission artifacts if deletion is
  performed so the cleanup remains auditable.

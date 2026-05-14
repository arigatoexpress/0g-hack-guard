# X Media Cleanup Runbook

This is the safe path for Ari's request to remove non-submission X posts/media
after the HackQuest project is submitted.

## Boundary

- Do not delete posts directly from browser memory, screenshots, or stale local
  assumptions.
- Keep the submitted HackQuest proof post by default:
  `https://x.com/rariwrldd/status/2054779961425461542`.
- Keep the follow-up guardrail-engine post by default:
  `https://x.com/rariwrldd/status/2055041461218140204`.
- Generate a manifest, review it, run a dry-run delete pass, then require fresh
  explicit confirmation for live deletion.

## Commands

Generate a template without X credentials:

```bash
.venv/bin/python scripts/x_media_cleanup.py --template --manifest-out content/x_media_cleanup_manifest.template.json
```

Generate a real review manifest from the authenticated account timeline.
Media-bearing posts only:

```bash
.venv/bin/python scripts/x_media_cleanup.py --manifest-out content/x_media_cleanup_manifest.review.json
```

All recent posts, including text-only posts:

```bash
.venv/bin/python scripts/x_media_cleanup.py --all-posts --manifest-out content/x_media_cleanup_manifest.review.json
```

If X API credentials are unavailable but Ari has an authenticated Brave/Chromium
session open on the local DevTools port, generate the same review manifest from
that browser session without saving cookies or auth headers:

```bash
PYTHONPATH=src .venv/bin/python scripts/x_brave_timeline_manifest.py --manifest-out content/x_media_cleanup_manifest.review.json
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
- Add any HackQuest/0guard wording that should survive with `--keep-keyword`.
- The default keep keywords preserve obvious 0guard / 0G / HackQuest posts.
- Save the reviewed manifest next to the submission artifacts if deletion is
  performed so the cleanup remains auditable.

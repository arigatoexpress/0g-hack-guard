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
- If a project X account is created, do not invent account identity fields.
  The public-safe project values are: display name `0guard`, bio from
  `content/project_x_account_kit.json`, proof page as the website, and the
  generated 0guard logo as the avatar. Email/phone, date of birth, password,
  and verification codes must stay operator-controlled and must not be stored in
  the repo.

## Current Browser Findings - 2026-05-14

- Main X account confirmed active in Brave as `@rariwrldd`.
- Profile currently reports 2,563 posts, so full cleanup is not realistic as a
  manual click-through task.
- X account switcher in the logged-in session exposed only `Add an existing
  account` and `Log out @rariwrldd`; the direct logged-in signup URL returned
  X's generic error page.
- Brave private-window signup opens successfully and reaches the `Create your
  account` form. The next required fields are real email/phone and date of
  birth, followed by platform verification.
- No X API credentials are present in the local environment. The available CDP
  endpoint on port 9222 belongs to a Chrome session, not the Brave X session.
  Use the API path below or restart Brave with a controlled CDP session before
  attempting bulk cleanup.

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

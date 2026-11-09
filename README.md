# Civitai Music Discovery Preview

An independent music/video discovery fork of **Civitai Artist Discovery**, with
configurable collection feeds, collection statistics and guarded curation actions.
It runs separately from Civitai Companion and uses its own profile.

Based on the [original project](https://github.com/theevildarkmage-hue/Civitai-Artist-Discovery)
and [bno84's music work](https://github.com/bno84/Civitai-Artist-Discovery/tree/dev-v3).
This is a community project, not an official Civitai product.

## What is included

- Music Scout: videos with sound, keyboard navigation, saved viewing progress,
  music-model-attributed queues and a per-creator cap.
- Configurable Civitai collections, each with a video queue and a creator feed.
- Optional comments when saving a video, reviewed before sending; leave the
  comment blank to save without posting.
- Collectalytics: collection statistics, creator breakdowns, additions over time,
  known video duration, copyable summaries and submission review.
- The original artist browser, local history, taste profile and content controls.
- Current upstream privacy/recovery improvements plus stricter decoder, logging,
  consent, cooldown and duplicate-comment protections.

## Run from source

Use Python **3.11 or newer** on Windows, with a modern browser. In this checkout:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py --stable
```

The stable-source entry point uses `data-music-discovery/` beside this source tree.
A plain development launch uses `data-music-development/`. Neither automatically
loads an original Discovery or Companion profile. Keep each profile intact,
including its protected credentials and `discovery/comment-outcomes.sqlite3`.

Open **Music Scout → Collections & privacy** to add collection IDs or Civitai
collection links. Up to twelve collections are supported. Initial suggested feeds
can be removed or renamed locally without changing anything on Civitai.

Linux source/Podman support is inherited and has not been verified on a physical
Linux desktop in this update. The container expects a desktop session/keyring;
it is not a recipe for publishing an unauthenticated network service.

## Account actions and privacy

Hosted Community and activity reporting are **off by default** and have separate
local opt-ins. Civitai sign-in and personal browsing work without Community enrollment.
Enabling it shares the public account identity with the original author's service;
optional activity reporting additionally shares usage time, version and platform.
Turning it off does not delete records already held there.

This fork accepts connections only from this device. LAN sharing is disabled
pending authenticated client access. New diagnostic records contain fixed operation,
status and category fields; historical logs and personal galleries remain local data.

Comments and collection changes are never automatically replayed. If a compound
action has an uncertain or partial outcome, the app blocks repetition even after
restart. Inspect and complete it on Civitai. Clearing the profile would also remove
that protection, so retain the outcome journal.

The original author's binary updater is not used for this fork. Update checks point
here and default off; automatic binary installation is disabled. This update delivers
source, not a signed installer or a published Windows executable.

## Validation and development

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/run_tests.py --only music_reliability music_settings_browser music_scout music_scout_http collectalytics_http
```

Tests use isolated profiles and synthetic accounts. Do not replace test fixtures with
real credentials. Live authenticated posting is not part of the automated checks.

- [Implementation, migrations and tradeoffs](docs/MUSIC-FORK.md)
- [Exact verification and outstanding acceptance](docs/MUSIC-VERIFICATION.md)
- [Preserved upstream README](UPSTREAM-README.md) — original-project guidance;
  the fork's setup and privacy behavior above take precedence.
- [MIT license and attribution](LICENSE)

Music discovery uses resource credits rather than audio recognition. Videos loop;
600 milliseconds on screen counts as viewed. Collection figures are bounded curation
statistics, not listener analytics. Native playback and live account compatibility
still require user acceptance.

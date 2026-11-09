# Music fork verification — November 9, 2026

## Scope and results

Verified on Windows with an isolated CPython 3.12.15 environment, Pillow 13.0.0,
Playwright Chromium 149.0.7827.55 and synthetic accounts. The test runner created
separate temporary profiles and ports. An additional socket guard blocked non-loopback
test traffic. No real credentials, account reads, comments, reactions or collection
changes were used. Browser tests demonstrate mocked behavior, not live Civitai acceptance.

The final targeted selection contains **34 passing suites, zero skips**. The first
32-suite pass had two assertion failures: old app naming and old settings defaults.
Those expectations were corrected, retaining content-setting preservation and layout
assertions, and both suites passed in a separate rerun. Earlier failing run receipts
remain local rather than being overwritten.

| Area | Exact suites, all passed |
| --- | --- |
| Music and collections | `music_reliability`, `music_settings_browser`, `music_scout`, `music_scout_http`, `music_scout_browser`, `collectalytics_http`, `collectalytics_browser` |
| Writes, cooldowns and diagnostics | `social_comments`, `read_retry_correctness`, `api_failure_diagnostics`, `browser_diagnostics`, `community_safe_diagnostics` |
| Content controls and layout | `resource_bounds`, `content_control_recovery`, `content_filter_toggles_http`, `content_controls`, `content_level_settings`, `content_filter_cache`, `community_filters_browser`, `header_polish_browser`, `time_machine_ui` |
| Identity, persistence and boundaries | `oauth_identity`, `oauth_storage`, `oauth_refresh_race`, `oauth_disconnect`, `registry`, `lan_security`, `source_hygiene`, `persistence_cache`, `audit_http_boundaries`, `security_smoke`, `stable_source` |
| Synthetic identity-policy regression checks | `git_identity_guard`, `personal_identity_privacy` |

The two additional identity suites contain 28 Git/hook cases and 16 personal-data
redaction cases. The Git-hook suite first encountered the host's Windows Store Python
alias; rerunning with the isolated environment's Python first on the test PATH passed.
These tests use synthetic private policies, never the original author's private data.

`music_reliability` contains 18 focused cases: durable partial/uncertain outcomes,
concurrent journal instances, account separation and account-pinned writes, comment
creation-ID validation, collection validation/persistence/escaping, stale queue
invalidation, numeric and HTTP-date cooldowns including HTML 429/503, long deadlines,
fixed diagnostics, cloud opt-out including immediate revocation, sign-in without cloud
enrollment, legacy LAN preferences, MIME filtering and format-restricted decoding.

The collection-editor browser suite tests add/edit/remove/save/reload, URL-to-ID
conversion, escaped names/comments, duplicate rejection and consent controls at six
viewport sizes from 320 px to 1440 px. Header/navigation checks passed at 320, 390,
768 and 1440 px. Other browser suites cover the imported Music Scout, Collectalytics,
content controls and Time Machine flows with mocked responses.

## Source and dependencies

All tracked Python files parse; changed JavaScript passes `node --check`. Git whitespace
checks and the repository source-hygiene gate pass. The preserved upstream README is
byte-identical in Git to upstream commit `2e851060a2c0c315c4f8dfd0e5ce65a97f830ce4`.

`pip check` passed. An OSV query of all 18 installed packages in the isolated Windows
runtime/development environment returned no advisory matches after updating Pillow
and the environment's pip. This is a dated database result, not a malware or security
certification. Linux-only dependencies, operating-system libraries, browser binaries
and hosted service deployments were outside that dependency scan.

The upstream release identity-policy tooling is retained. Its full publication gates,
installer/update simulation matrix and all other pre-existing suites outside the
34 listed above were not rerun. No fork binary build, installer, release upload,
native Linux/Podman run or automatic update installation was performed.

Post-push CI exposed an inherited deployment prerequisite: the author's Git identity
audit needs a private policy unavailable in this fork. That job is now restricted to
the original repository, with a separate credential-free source-hygiene job for this
fork's committed pushes, schedules and manual runs. This is not a substitute for the
author's private identity audit or the unexecuted release gate.

## Data integrity and outstanding acceptance

Settings regressions verify sparse-profile defaults and preservation of existing
content selections. Invalid collection definitions cannot become outbound request
URLs. New cloud opt-ins default off and old LAN-on settings are ignored. Runtime
profile selection is fork-specific; no original Discovery or Companion profile was
opened, migrated or overwritten. The new SQLite outcome journal is additive and
retains hashed operation keys across restart. Removing the profile also removes its
duplicate-action protection. Existing historical logs are preserved.

Live OAuth, playback with sound, collection ownership/grants, reaction behavior,
real API compatibility and optional hosted participation still need user acceptance.
No authenticated posting test is implied. Uncertain comment/collection outcomes are
deliberately reconciled on Civitai; the app cannot make two remote writes atomic.
Thumbnail decoding remains in-process. Music categorization uses resource attribution;
collection metrics are bounded curation statistics, not listening statistics.

The next milestone is a source smoke test with a real account using read-only browsing
and playback, followed by a separately reviewed fork packaging/update channel.
Any live posting test needs an explicit selected action and authorization.

Implementation and provenance: [MUSIC-FORK.md](MUSIC-FORK.md).

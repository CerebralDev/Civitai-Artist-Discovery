# Music Discovery fork — November 9, 2026

## Sources and implementation

This independent fork combines original upstream `2e851060a2c0c315c4f8dfd0e5ce65a97f830ce4`
with bno84's `dev-v3` music/collection work at
`906aa83f99176aaf751fc97129f5c40c5d4b666d`. The 47-file feature delta was applied onto
the newer upstream tree, preserving its identity-redaction, package-audit and recovery
changes. Upstream rewrote part of its history; tree comparison, rather than commit counts
against current main, establishes what was integrated. Original authors retain attribution
and the upstream license remains intact.

This application shares no source, account configuration, installation or runtime data
with Civitai Companion. It is a separate Python/browser application.

Music Scout supplies video listening queues, per-creator limits, music-model-attributed
feeds, saved viewing progress, keyboard controls, original-file playback with a transcode
fallback, reactions and configurable collections. Collectalytics supplies collection
statistics and submission review. Local content-filter switches and source-channel
indicators from the music fork are retained.

## Collection preferences

Open **Music Scout → Collections & privacy**. Add up to twelve collections using a
numeric Civitai collection ID or an HTTPS civitai.com/civitai.red collection link. Give
each a local display name and, optionally, a plain-text comment to show before saving
a video. A blank comment saves without posting. Names/comments are escaped for display;
resource URLs and queue identifiers are generated locally from validated numeric IDs.

Each collection has a recently-added video queue and a creator feed. Music Focus and
H3 Movies Museum are initial suggestions, with **no automatic promotional comment**.
They can be renamed locally or removed. Removing a feed does not alter the collection
on Civitai. Adding a video is offered only when Civitai reports that the account can
write to the selected collection. Submission review separately requires the appropriate
collection and social permissions.

Settings are saved atomically and preserved across ordinary preference changes.
Missing new fields receive defaults. Malformed collection definitions fail closed to
an empty list rather than becoming request URLs. Duplicate IDs and oversized lists are
rejected. Configuration/account/content-policy changes invalidate in-memory music
queues; late queue responses cannot repopulate a changed session. Other tabs receive
settings-change notifications.

## Reliability fixes and root causes

**Compound writes:** posting a comment and adding/accepting a collection item are two
independent remote operations. Previously, an acceptance failure or lost comment response
allowed a later manual attempt to post again. A SQLite outcome journal now writes an
intent before sending, records confirmed comment/completion states, and blocks repeated
attempts across concurrent requests and process restarts. Keys are hashes of account,
operation, collection and item; the journal contains no comment text or credentials.
Comment success also requires a positive creation ID. Writes remain single-attempt.

Uncertain or partial outcomes must be inspected and completed on Civitai. There is no
automatic reset or repost button. This intentionally favors avoiding duplicate comments
over retry convenience. Even a failure before a remote write can leave a conservative
barrier. Local storage cannot provide atomicity with Civitai; retaining the profile and
journal is essential. Account-bound clients reject a changed identity before sending.

**Cooldowns:** the music fork's parallel public transport bypassed shared pacing and
ignored HTTP-date Retry-After. Music hub reads now use the existing archive request lane.
Social errors propagate cooldowns, and interactive requests respect the shared deadline.
HTTP status/headers are processed before parsing error bodies. Numeric/date headers are
supported; 429 without a usable header retains a 60-second fallback. A long server wait
survives retry-budget exhaustion. This makes large creator hubs slower than unpaced
parallel requests but avoids simultaneous workers repeatedly hitting the same limit.

**Thumbnail decoder:** Pillow is upgraded from 12.3.0 to 13.0.0, requiring Python 3.11+.
Content-Type is checked before decoding. Header/full-image opens explicitly permit only
JPEG, PNG, WebP and AVIF. Existing host, redirect, byte, pixel and concurrency bounds
remain. The decoder still runs in-process; a separate decoder process is not implemented.

**Test cleanup:** Music Scout now exposes explicit connection closure, used at app
shutdown and by tests. The previously failing Windows test closes its second SQLite
connection instead of relying on garbage collection. The content-controls fixture now
marks its synthetic image details complete, preventing unintended external enrichment.

## Privacy and isolation

- Hosted Community enrollment/renewal and registry activity are separately opt-in.
  Both default off, including for settings files created before these fields existed.
  Civitai sign-in and personal browsing continue without a cloud identity handshake.
  Requests to the hosted service check current local consent at the transport boundary.
  Turning participation off stops new requests but does not erase records already held
  by that service or cancel a request already sent. Community still uses the author's
  service and registered OAuth integration when explicitly enabled.
- LAN sharing is disabled in this fork. The server binds to loopback, refuses an
  all-interface override and rejects remote-host access. Authenticated LAN pairing is
  deferred rather than exposing the host's account to unauthenticated peers.
- New API failure/browser/error logs retain fixed status/category/operation fields,
  not bodies, resource URLs, account names, prompts or arbitrary exception text. Existing
  historical logs are preserved and are not retroactively sanitized. Developer-only
  inspection tools and ordinary gallery databases are not anonymized support exports.
- Stable source uses `data-music-discovery/`; development source uses
  `data-music-development/`. Existing original Discovery and Companion profiles are not
  selected or migrated. An explicit `CIVITAI_HISTORY_DATA_DIR` remains available for
  isolated tests or deliberate profile selection.
- The app is labeled **Civitai Music Discovery Preview**. Update lookup points to this
  fork, checks default off, and automatic binary installation is disabled until a
  separately verified fork release channel exists. Do not use an original-author binary
  as a replacement for this source tree.

## Limits and acceptance

Music detection uses resource attribution, not audio recognition. Videos loop rather
than advancing automatically, and 600 ms on screen marks an item viewed. Collection
followers are derived from contributor metadata; durations depend on available video
metadata. Collection reports are bounded to 10,000 accepted items and 1,000 review items,
with truncation indicated. These are curation statistics, not listener analytics.

Automated validation uses isolated profiles, synthetic accounts, mocked Civitai services
and blocked external test traffic. Browser tests exercise interface behavior and layout,
not real audio playback or live API compatibility. No authenticated posting test was
performed. Native playback, OAuth with a real account, collection ownership/grants and
hosted opt-in acceptance remain user checks. No Windows installer or executable is
published by this source update. The author's release packaging/privacy-policy tooling
is retained; independently publishing binaries needs a fork-specific release process.

See [verification record](MUSIC-VERIFICATION.md) for exact suites and remaining limits.

# Changelog

All notable changes to LLM Fusion.

## Unreleased

### Added
- **Grok (xAI) as a 4th provider.** New `GrokAdapter` (`council_runner/adapters/grok.py`) drives the xAI Grok Build CLI (`grok`) in headless read-only mode (`-p … --output-format json --permission-mode plan --no-memory --no-subagents --verbatim --tools ""`), with a defensive extractor that tolerates json / streaming-json / plain-text output. Registered in the adapter registry; `roles/realist.md` adds the *realist* lens (live market/world reality, timing, data-grounded risk). Roster: `grok-realist` joins `advise_agents` (now 7 lenses across 5 models) and `grok-builder` joins `execute_agents` (4 models). Grok advises and plans only — it never executes; the autonomous executor stays codex-only. Verified live against `grok` 0.2.77 (`--doctor --ping`).
- **`GeminiAdapter` — a latent gemini-cli fallback for the Google seat** (`council_runner/adapters/gemini.py`). Registered but **not** wired into `agents.yaml` (antigravity/`agy` stays the active Google seat); a drop-in for environments where Antigravity isn't installed or the Gemini tier doesn't grant Antigravity quota — activate by swapping `cli: antigravity` → `cli: gemini` in the roster. The fallback uses `--approval-mode plan --sandbox` and keeps YOLO off.
- Seal hardened — anonymization patterns and the round-1 prompts now strip Grok/xAI self-references too.
- Test coverage for both new providers (argv construction, executor-guard refusal, self-reference stripping) + updated roster-count assertions.

### Changed
- Sonnet seat (`claude-firstprinciples`) pinned to **`claude-sonnet-5`** (released 2026-06-30, narrows the gap with Opus 4.8). If you'd rather the `sonnet` alias auto-track future releases, that's a one-line revert.
- Switched the Google provider surface from `gemini` CLI to `antigravity` CLI while keeping Gemini model names in the roster.
- Pointed the Antigravity provider at the installed `agy` executable.

## [1.2.0] — 2026-06-16

### Added
- **Packaged as a self-contained Claude Code plugin + marketplace.** The repo is now a marketplace (`.claude-plugin/marketplace.json`) hosting the `llm-fusion` plugin (`plugins/llm-fusion/`) — members `/plugin marketplace add` + `/plugin install`, no separate clone needed.
- Runs + member config moved to a **persistent home** (`~/.llm-council/`, or `${CLAUDE_PLUGIN_DATA}`), never the read-only plugin dir; skills self-locate the bundled runner via `${CLAUDE_PLUGIN_ROOT}` with a cache-glob fallback.

## [1.1.0] — 2026-06-16

### Added
- **Auth via `claude setup-token`** — runner auto-loads `CLAUDE_CODE_OAUTH_TOKEN` from a gitignored `.env.local`, so the claude seat works even when the macOS keychain token is stale.
- **Two rosters** in `agents.yaml`: `advise_agents` (6 diverse lenses across 4 models) and `execute_agents` (a build-off — one shared `builder` role per distinct model).
- **`roles/builder.md`** — the shared execution role for the execute build-off.
- **Live progress output** — per-agent fan-out + `✓/✗` completion lines to stderr.
- Retryable **`EMPTY`** status — gemini `INVALID_STREAM` / empty responses now retry instead of dropping a model.

### Changed
- Skills renamed: `/council-advise` → **`/fusion-council`**, `/council-execute` → **`/fusion-build`**.
- gemini model bumped `gemini-2.5-pro` → **`gemini-3.1-pro-preview`** (current flagship on the CLI).
- Execute mode is now a **model build-off** (same builder role, different models, judge fuses the best) instead of reusing the advise lenses.

## [1.0.0] — 2026-06-14

### Added
- Sealed multi-model council runner: `claude` + `codex` + `gemini` answer independently in parallel, anonymized A/B/C, fresh judge synthesizes.
- **Advise** mode (decision memo) and **execute** mode (plan → spec → sandboxed build → audit).
- Two judge backends: `handoff` (calling session judges) and `auto` (self-contained CLI judge).
- Hardened **codex sandbox executor** (pinned writable roots, tmp excluded, network off) — escape-proof, proven by `tests/test_sandbox_escape.py`.
- `--doctor` / `--doctor --ping` readiness checks; graceful degradation (quorum + diversity warning); zero runtime deps.

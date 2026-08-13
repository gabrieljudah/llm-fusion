# LLM Fusion — a Claude Code plugin

> *Many models in. One fused answer out.*

A **sealed multi-model LLM council** for Claude Code. One prompt → **Claude + Codex (GPT) + Antigravity (Gemini) + Grok (xAI) answer independently** (no peeking at each other) → anonymized → a judge fuses the best. Two commands:

- **`/fusion-council "<question>"`** — choose Claude Fable 5, Claude Opus 4.8, Codex GPT5.6 sol, Gemini 3.1, and/or Grok 4.6; 7 expert lenses pressure-test the decision → one judged memo.
- **`/fusion-build "<goal>"`** — choose at least 3 models for a sealed build-off; the judge fuses the best plan, then it gets built and audited.

This repo is both the **plugin** and its **marketplace** (the catalog Claude Code installs from).

## Install (members)

**Prerequisites — you need all four CLIs installed and logged in, plus Python 3.11+:**
- [`claude`](https://docs.claude.com/en/docs/claude-code) (Claude subscription)
- `codex` (ChatGPT/Codex subscription)
- `agy` (Google Antigravity CLI / Gemini subscription)
- `grok` (xAI Grok CLI access)

Then, in Claude Code:

```
/plugin marketplace add gabrieljudah/llm-fusion
/plugin install llm-fusion@fusion
```

Verify your setup from a checkout:

```
cd plugins/llm-fusion
python3 -m council_runner --doctor
```

That's it — `/fusion-council` and `/fusion-build` are now available. Each asks which models to include; choose at least 3 across 2 providers, or use all five. Run folders are written to `~/.llm-council/council-runs/` (never inside the plugin).

## Update

```
/plugin marketplace update fusion   →   /reload-plugins
```

Auto-update can be toggled in `/plugin` → Marketplaces. Each release bumps the version in `plugin.json` + `marketplace.json` and is git-tagged (`v1.2.0`, …); see [the plugin CHANGELOG](plugins/llm-fusion/CHANGELOG.md).

## What's inside

```
.claude-plugin/marketplace.json        the catalog (this repo = a marketplace)
plugins/llm-fusion/                 the plugin payload (self-contained)
  .claude-plugin/plugin.json            the plugin manifest
  skills/fusion-council/SKILL.md        /fusion-council  (decide)
  skills/fusion-build/SKILL.md          /fusion-build    (build)
  council_runner/                       the Python engine (zero runtime deps)
  roles/  prompts/  agents.yaml         the council config (editable)
  tests/                                unit + live sandbox-escape tests
```

Full usage + design: [plugins/llm-fusion/README.md](plugins/llm-fusion/README.md).

## Note on cost / access
The council uses the subscriptions behind the models selected for each run. It's a power-user tool — members need each selected provider CLI installed and authenticated.

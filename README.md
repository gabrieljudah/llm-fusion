# LLM Fusion — a Claude Code plugin

> *Many models in. One fused answer out.*

A **sealed multi-model LLM council** for Claude Code. One prompt → **Claude Fable 5.1 + Codex GPT-6 Astra + Grok 4.6 answer independently** (no peeking at each other) → anonymized → a judge fuses the best. Two commands:

- **`/fusion-council "<question>"`** — Fable 5.1, GPT-6 Astra, and Grok 4.6 wear 7 expert lenses to pressure-test the decision → one judged memo.
- **`/fusion-build "<goal>"`** — all three models plan the same job in a sealed build-off; the judge fuses the best plan, then it gets built and audited.

This repo is both the **plugin** and its **marketplace** (the catalog Claude Code installs from).

## Install (members)

**Prerequisites — you need all three CLIs installed and logged in, plus Python 3.11+:**
- [`claude`](https://docs.claude.com/en/docs/claude-code) (Claude subscription)
- `codex` (ChatGPT/Codex subscription; version 0.153 or newer for GPT-6 Astra)
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

That's it — `/fusion-council` and `/fusion-build` are now available. Each runs the full three-model council (Fable 5.1, GPT-6 Astra, Grok 4.6). Run folders are written to `~/.llm-council/council-runs/` (never inside the plugin).

## Update

```
/plugin marketplace update fusion
/plugin update llm-fusion@fusion
/reload-plugins
```

Refreshing the marketplace alone does **not** update an already-installed plugin; run the explicit plugin update step above. Auto-update can be toggled in `/plugin` → Marketplaces. Each release bumps the version in `plugin.json` + `marketplace.json` and is git-tagged; see [the plugin CHANGELOG](plugins/llm-fusion/CHANGELOG.md).

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

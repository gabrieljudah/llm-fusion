---
name: fusion-council
description: Run a decision, question, or tradeoff through the LLM Fusion sealed multi-model council (claude + codex + antigravity + grok answer independently, anonymized), then synthesize the verdict AS the Judge. Use when the user says "fusion-council", "fusion council", "fusion this", "sealed council", "run the fusion council", or wants real different models (not in-Claude lenses) to pressure-test a decision and hand it back for a judged verdict. For the lighter in-Claude lenses tool use /council instead; to BUILD something use /fusion-build.
---

# fusion-council — sealed multi-model council (advise mode)

You orchestrate a **sealed council** of real, different models, then you are the **Judge**. The runner enforces the seal (independent parallel processes, no cross-talk, anonymized answer letters). You synthesize.

## Steps

1. **Let the user choose the models.** Ask one multi-select question with these exact options: **Claude — Fable 5**, **Claude — Opus 4.8**, **Codex — GPT5.6 sol**, **Gemini — 3.1**, **Grok — 4.6**. Require at least 3 choices across at least 2 providers. If the user says “all” or does not want to choose, use all five.

2. **Run the council** (advise mode, you judge). Locate the bundled runner, then run it with one `--model` flag per choice:
   ```bash
   PLUGIN="${CLAUDE_PLUGIN_ROOT:-$(ls -d "$HOME"/.claude/plugins/cache/*/llm-fusion/*/ 2>/dev/null | sort -V | tail -1)}"
   PLUGIN="${PLUGIN:-$HOME/projects/llm-fusion/plugins/llm-fusion}"
   cd "$PLUGIN" && python3 -m council_runner --mode advise --judge handoff \
     --model "<fable-5|opus-4.8|gpt-5.6-sol|gemini-3.1|grok-4.6>" \
     --model "<second choice>" --model "<third choice>" \
     --brief "<the user's question, verbatim or lightly cleaned>"
   ```
   It fans out to the roster in `agents.yaml`, runs sealed Round 1 in parallel, anonymizes, and exits `awaiting-judge`, printing the run path (under `~/.llm-council/council-runs/`).

3. **Read ONLY the anonymized answers.** Read `<run>/JUDGE_INSTRUCTIONS.md` and every file in `<run>/public/answers/` (A.md, B.md, …). **Do NOT open `mapping.json`** — that would de-anonymize the council and defeat the seal.

4. **Judge.** Follow the structure in JUDGE_INSTRUCTIONS verbatim (Recommendation / Confidence / Where they agree / Where they disagree + your ruling / Key risks / Next actions). Weigh the arguments on merit. Write your synthesis to `<run>/public/final_report.md`, starting with the header line `> **Council run** · Judge: main-session (handoff) · Models: …` copied from `<run>/meta.json` (`models_surviving`), plus any `diversity_notes`.

5. **Show the range, then the verdict (transparency).** Because the run is a blocking subprocess the user can't watch live, surface what each member contributed BEFORE your synthesis: a one-line-per-answer summary (each answer letter → its recommendation + confidence) so they see the spread of views, not just your conclusion. Then give the verdict + run path. Confirm `final_report.md` exists and is non-empty. If `meta.json` has a DIVERSITY WARNING (fewer than 3 models survived — e.g. a CLI was unauthenticated), surface it plainly and suggest re-running after fixing auth.

The full advise council is **7 lenses across 5 selectable models** (architect, pragmatist, skeptic, first-principles, operator, user-advocate, realist). You may widen or narrow lenses only within the five routes shown by `python3 -m council_runner --list-models`; unsupported custom model IDs fail loudly.

## Notes
- **Don't answer from your own reasoning first.** The whole point is the sealed council; run it, then judge what it produced.
- A failed agent (not-authenticated / rate-limited / timeout) is handled gracefully — the council proceeds on quorum (≥2 answers from ≥2 providers). If it aborts below quorum, relay the actionable error.
- For a **fully unattended / headless** run (no main-session judging), use `--judge auto` instead — the runner spawns a fresh judge CLI and writes `final_report.md` itself.
- Doctor check before a run if unsure: `cd "$PLUGIN" && python3 -m council_runner --doctor` (verifies the member has claude + codex + agy + grok installed + authenticated).

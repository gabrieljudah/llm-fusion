---
name: fusion-build
description: Run a build goal through the LLM Fusion council in EXECUTE (fusion) mode — claude + codex + antigravity + grok each PLAN it independently (same builder role), anonymized, then you synthesize one execution spec AS the Judge and build it. Use when the user says "fusion-build", "fusion build this", "have the council build", or wants multiple real models to independently plan a task before one synthesized plan is executed. For decisions/advice (no building) use /fusion-council.
---

# fusion-build — sealed multi-model council (execute / fusion mode)

This is a **build-off**: the selected planning models each plan the goal **wearing the SAME builder role** — so the diversity is purely *how each model executes the same task*, not different personalities. You are the **Judge**: fuse the best of each into one execution spec, then **work on it**. (Contrast advise mode, where the agents wear *different* lenses.)

## Steps

1. **Let the user choose the planning models.** Ask one multi-select question with these exact options: **Claude — Fable 5**, **Claude — Opus 4.8**, **Codex — GPT5.6 sol**, **Gemini — 3.1**, **Grok — 4.6**. Require at least 3 choices across at least 2 providers. If the user says “all” or does not want to choose, use all five.

2. **Run the planning council** (execute mode, you judge). Locate the bundled runner, then run it with one `--model` flag per choice:
   ```bash
   PLUGIN="${CLAUDE_PLUGIN_ROOT:-$(ls -d "$HOME"/.claude/plugins/cache/*/llm-fusion/*/ 2>/dev/null | sort -V | tail -1)}"
   PLUGIN="${PLUGIN:-$HOME/projects/llm-fusion/plugins/llm-fusion}"
   cd "$PLUGIN" && python3 -m council_runner --mode execute --judge handoff \
     --model "<fable-5|opus-4.8|gpt-5.6-sol|gemini-3.1|grok-4.6>" \
     --model "<second choice>" --model "<third choice>" \
     --brief "<the build goal>" [--workspace <abs path to the repo/dir to build in>]
   ```
   Each planning model produces a PLAN for the same goal (same builder role), sealed and anonymized. The runner exits `awaiting-judge` with the run path. Pass `--workspace` when the work targets an existing project; omit it for greenfield.

3. **Read ONLY the anonymized plans.** Read `<run>/JUDGE_INSTRUCTIONS.md` and `<run>/public/answers/*.md`. **Do NOT open `mapping.json`.**

4. **Synthesize the spec.** Following JUDGE_INSTRUCTIONS, write one execution spec to `<run>/execute/execution_spec.md` (Objective / Steps / Executor prompt / Auditor checklist / Done-when), taking the best ideas across the plans.

5. **Execute it — "work on it".** Build the deliverable directly in this session against the real target (the `--workspace` path or wherever the user wants it). You are the executor: implement the spec, then verify it against the spec's auditor checklist.

6. **Report.** Summarize what you built, where, and the audit result, plus the run path.

## Notes
- **Default = you build it** (handoff). The Judge synthesizes the plan and you build it.
- For **fully autonomous, sandboxed** execution (no human in the loop), use `--judge auto`: the runner spawns a fresh judge to write the spec, runs a **codex executor in an isolated git-init'd sandbox** (writable-roots pinned, network off — it cannot touch real files), then an **antigravity auditor**, and writes `final_report.md` with the deliverable + audit. Use this when you want the council to build unattended; use handoff when you want to build in the live project yourself.
- Codex is the only autonomous executor (it's the only CLI with a real OS sandbox). claude/antigravity/grok executors are v2.

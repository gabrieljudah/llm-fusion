"""Member-facing LLM Fusion model catalog and roster selection.

The catalog is the single translation layer between stable labels shown to a
member and the provider-specific model IDs passed to each CLI.  Keep release
updates here instead of scattering display names and IDs through skills/tests.

v1.5 roster (2026-09-05): Claude Fable 5.1, Codex GPT-6 Astra, Grok 4.6 — one
frontier model per vendor.  Opus 4.8 and Gemini 3.1 (Antigravity) were retired
from the shipped catalog; the antigravity/gemini adapters stay in the tree as
latent fallbacks and can be re-listed here in one line.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .core import AgentSpec, RosterConfig


@dataclass(frozen=True)
class ModelChoice:
    key: str
    display: str
    provider: str
    cli: str
    model: str


MODEL_CHOICES: tuple[ModelChoice, ...] = (
    ModelChoice("fable-5.1", "Fable 5.1", "Claude", "claude", "claude-fable-5-1"),
    ModelChoice("gpt-6-astra", "GPT-6 Astra", "Codex", "codex", "gpt-6-astra"),
    ModelChoice("grok-4.6", "Grok 4.6", "Grok", "grok", "grok-4.6"),
)

BY_KEY = {choice.key: choice for choice in MODEL_CHOICES}
BY_ROUTE = {(choice.cli, choice.model): choice for choice in MODEL_CHOICES}
DEFAULT_MODEL_KEYS = tuple(choice.key for choice in MODEL_CHOICES)


def model_help() -> str:
    return ", ".join(f"{c.key} ({c.provider}: {c.display})" for c in MODEL_CHOICES)


def _selected_specs(specs: list[AgentSpec], selected: set[str]) -> list[AgentSpec]:
    return [spec for spec in specs if BY_ROUTE.get((spec.cli, spec.model), None)
            and BY_ROUTE[(spec.cli, spec.model)].key in selected]


def select_models(roster: RosterConfig, keys: list[str] | tuple[str, ...] | None) -> RosterConfig:
    """Return a roster restricted to member-selected catalog entries.

    No selection means the shipped default (all current model choices).
    At least three distinct models and two providers are required so a user
    cannot accidentally turn Fusion into a same-vendor echo chamber.  With the
    v1.5 three-model catalog that means the full council runs every time.
    """
    requested = list(keys or DEFAULT_MODEL_KEYS)
    unsupported = sorted({
        f"{spec.cli}/{spec.model}"
        for spec in roster.advise_agents + roster.execute_agents
        if (spec.cli, spec.model) not in BY_ROUTE
    })
    if unsupported:
        raise ValueError(
            "roster contains model routes outside the current model catalog: " + ", ".join(unsupported)
        )
    unknown = sorted(set(requested) - set(BY_KEY))
    if unknown:
        raise ValueError(f"unknown model choice(s): {', '.join(unknown)}")
    selected = set(requested)
    choices = [choice for choice in MODEL_CHOICES if choice.key in selected]
    providers = {choice.provider for choice in choices}
    if len(choices) < 3 or len(providers) < 2:
        raise ValueError("select at least 3 models across at least 2 providers")

    advise = _selected_specs(roster.advise_agents, selected)
    execute = _selected_specs(roster.execute_agents, selected)
    expected_routes = {(choice.cli, choice.model): choice.key for choice in choices}
    advise_routes = {(spec.cli, spec.model) for spec in advise}
    execute_routes = {(spec.cli, spec.model) for spec in execute}
    missing = sorted({
        key
        for route, key in expected_routes.items()
        if route not in advise_routes or route not in execute_routes
    })
    if missing:
        raise ValueError("missing requested model routes in roster: " + ", ".join(missing))

    # Auto-mode seats follow the chosen provider CLIs: judge rides the Claude
    # seat, the sandboxed executor rides Codex, the independent auditor rides
    # whichever CLI agents.yaml names (Grok by default — a third vendor).
    selected_by_cli = {choice.cli: choice for choice in choices}
    judge = dict(roster.judge)
    executor = dict(roster.executor)
    auditor = dict(roster.auditor)
    for seat in (judge, executor, auditor):
        cli = seat.get("cli", "")
        if cli in selected_by_cli:
            seat["model"] = selected_by_cli[cli].model
        else:
            seat["cli"] = ""
            seat["model"] = ""

    return replace(
        roster,
        judge=judge,
        executor=executor,
        auditor=auditor,
        advise_agents=advise,
        execute_agents=execute,
        selected_models=[choice.key for choice in choices],
    )

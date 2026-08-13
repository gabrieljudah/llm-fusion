"""Member-facing LLM Fusion model catalog and roster selection.

The catalog is the single translation layer between stable labels shown to a
member and the provider-specific model IDs passed to each CLI.  Keep release
updates here instead of scattering display names and IDs through skills/tests.
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
    ModelChoice("fable-5", "Fable 5", "Claude", "claude", "claude-fable-5"),
    ModelChoice("opus-4.8", "Opus 4.8", "Claude", "claude", "claude-opus-4-8"),
    ModelChoice("gpt-5.6-sol", "GPT5.6 sol", "Codex", "codex", "gpt-5.6-sol"),
    ModelChoice("gemini-3.1", "Gemini 3.1", "Gemini", "antigravity", "Gemini 3.1 Pro (High)"),
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

    No selection means the shipped default (all five current model choices).
    At least three distinct models and two providers are required so a user
    cannot accidentally turn Fusion into a same-vendor echo chamber.
    """
    requested = list(keys or DEFAULT_MODEL_KEYS)
    unsupported = sorted({
        f"{spec.cli}/{spec.model}"
        for spec in roster.advise_agents + roster.execute_agents
        if (spec.cli, spec.model) not in BY_ROUTE
    })
    if unsupported:
        raise ValueError(
            "roster contains model routes outside the v1.4 catalog: " + ", ".join(unsupported)
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
    if len({spec.model for spec in advise}) < 3 or len({spec.model for spec in execute}) < 3:
        raise ValueError("selected models are not fully represented in the shipped roster")

    # Auto-mode support follows the chosen provider seats. If both Claude
    # choices are present, Fable 5 remains the judge; otherwise use Opus 4.8.
    selected_by_cli = {choice.cli: choice for choice in choices}
    for choice in choices:
        if choice.key == "fable-5":
            selected_by_cli["claude"] = choice
            break
    judge = dict(roster.judge)
    executor = dict(roster.executor)
    auditor = dict(roster.auditor)
    if "claude" in selected_by_cli:
        judge["model"] = selected_by_cli["claude"].model
    else:
        judge["cli"] = ""
        judge["model"] = ""
    if "codex" in selected_by_cli:
        executor["model"] = selected_by_cli["codex"].model
    else:
        executor["cli"] = ""
        executor["model"] = ""
    if "antigravity" in selected_by_cli:
        auditor["model"] = selected_by_cli["antigravity"].model
    else:
        auditor["cli"] = ""
        auditor["model"] = ""

    return replace(
        roster,
        judge=judge,
        executor=executor,
        auditor=auditor,
        advise_agents=advise,
        execute_agents=execute,
        selected_models=[choice.key for choice in choices],
    )
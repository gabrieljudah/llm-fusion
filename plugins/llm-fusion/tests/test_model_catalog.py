"""Public behavior tests for member-selectable model routing."""
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from council_runner.cli import build_parser, main  # noqa: E402
from council_runner.model_catalog import BY_KEY, MODEL_CHOICES, select_models  # noqa: E402
from council_runner.orchestrator import load_roster  # noqa: E402
from council_runner.core import AgentSpec  # noqa: E402


class TestModelCatalog(unittest.TestCase):
    def setUp(self):
        self.roster = load_roster(ROOT / "agents.yaml")

    def test_catalog_preserves_requested_display_labels_and_callable_ids(self):
        expected = {
            "fable-5": ("Fable 5", "claude", "claude-fable-5"),
            "opus-4.8": ("Opus 4.8", "claude", "claude-opus-4-8"),
            "gpt-5.6-sol": ("GPT5.6 sol", "codex", "gpt-5.6-sol"),
            "gemini-3.1": ("Gemini 3.1", "antigravity", "Gemini 3.1 Pro (High)"),
            "grok-4.6": ("Grok 4.6", "grok", "grok-4.6"),
        }
        self.assertEqual(len(MODEL_CHOICES), 5)
        for key, (display, cli, model) in expected.items():
            choice = BY_KEY[key]
            self.assertEqual((choice.display, choice.cli, choice.model), (display, cli, model))

    def test_no_selection_uses_all_five_models(self):
        selected = select_models(self.roster, None)
        self.assertEqual(len({a.model for a in selected.execute_agents}), 5)
        self.assertEqual(selected.selected_models, [c.key for c in MODEL_CHOICES])
        self.assertEqual(selected.judge["model"], "claude-fable-5")
        self.assertEqual(selected.executor["model"], "gpt-5.6-sol")

    def test_member_can_select_three_models(self):
        selected = select_models(self.roster, ["opus-4.8", "gpt-5.6-sol", "gemini-3.1"])
        self.assertEqual(
            {a.model for a in selected.execute_agents},
            {"claude-opus-4-8", "gpt-5.6-sol", "Gemini 3.1 Pro (High)"},
        )
        self.assertEqual(selected.judge["model"], "claude-opus-4-8")

    def test_selection_rejects_fewer_than_three_models(self):
        with self.assertRaisesRegex(ValueError, "at least 3 models"):
            select_models(self.roster, ["fable-5", "gpt-5.6-sol"])

    def test_selection_does_not_reintroduce_excluded_auto_providers(self):
        selected = select_models(self.roster, ["opus-4.8", "gemini-3.1", "grok-4.6"])
        self.assertEqual(selected.judge["model"], "claude-opus-4-8")
        self.assertEqual(selected.executor["cli"], "")

        selected = select_models(self.roster, ["fable-5", "gpt-5.6-sol", "grok-4.6"])
        self.assertEqual(selected.auditor["cli"], "")

    def test_unsupported_custom_route_fails_loudly_instead_of_being_dropped(self):
        custom = AgentSpec("custom", "claude", "claude-sonnet-custom", "roles/architect.md")
        roster = replace(self.roster, advise_agents=self.roster.advise_agents + [custom])
        with self.assertRaisesRegex(ValueError, "outside the v1.4 catalog"):
            select_models(roster, None)

    def test_cli_accepts_repeated_model_flags(self):
        args = build_parser().parse_args([
            "--model", "fable-5",
            "--model", "gpt-5.6-sol",
            "--model", "grok-4.6",
            "--list-models",
        ])
        self.assertEqual(args.models, ["fable-5", "gpt-5.6-sol", "grok-4.6"])

    def test_list_models_does_not_depend_on_a_valid_roster(self):
        missing = str(Path(tempfile.mkdtemp()) / "missing-agents.yaml")
        self.assertEqual(main(["--agents", missing, "--list-models"]), 0)


if __name__ == "__main__":
    unittest.main()

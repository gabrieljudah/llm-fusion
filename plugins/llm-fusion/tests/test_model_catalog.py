"""Public behavior tests for the v1.5 model catalog and roster selection."""
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from council_runner.cli import _doctor, build_parser, main  # noqa: E402
from council_runner.model_catalog import BY_KEY, MODEL_CHOICES, select_models  # noqa: E402
from council_runner.orchestrator import load_roster  # noqa: E402
from council_runner.core import AgentSpec, Status  # noqa: E402

ALL_KEYS = ["fable-5.1", "gpt-6-astra", "grok-4.6"]
ALL_MODELS = ["claude-fable-5-1", "gpt-6-astra", "grok-4.6"]


class TestModelCatalog(unittest.TestCase):
    def setUp(self):
        self.roster = load_roster(ROOT / "agents.yaml")

    def test_catalog_preserves_requested_display_labels_and_callable_ids(self):
        expected = {
            "fable-5.1": ("Fable 5.1", "claude", "claude-fable-5-1"),
            "gpt-6-astra": ("GPT-6 Astra", "codex", "gpt-6-astra"),
            "grok-4.6": ("Grok 4.6", "grok", "grok-4.6"),
        }
        self.assertEqual(len(MODEL_CHOICES), 3)
        for key, (display, cli, model) in expected.items():
            choice = BY_KEY[key]
            self.assertEqual((choice.display, choice.cli, choice.model), (display, cli, model))

    def test_no_selection_uses_all_three_models(self):
        selected = select_models(self.roster, None)
        self.assertEqual(len({a.model for a in selected.execute_agents}), 3)
        self.assertEqual(len(selected.advise_agents), 7)
        self.assertEqual(selected.selected_models, ALL_KEYS)
        self.assertEqual(selected.judge, {"backend": "handoff", "cli": "claude", "model": "claude-fable-5-1"})
        self.assertEqual(selected.executor, {"cli": "codex", "model": "gpt-6-astra"})
        self.assertEqual(selected.auditor, {"cli": "grok", "model": "grok-4.6"})

    def test_explicit_full_selection_matches_default(self):
        selected = select_models(self.roster, ALL_KEYS)
        self.assertEqual({a.model for a in selected.execute_agents}, set(ALL_MODELS))

    def test_selection_rejects_fewer_than_three_models(self):
        with self.assertRaisesRegex(ValueError, "at least 3 models"):
            select_models(self.roster, ["fable-5.1", "gpt-6-astra"])

    def test_unknown_model_key_fails_loudly(self):
        with self.assertRaisesRegex(ValueError, "unknown model choice.*opus-4.8"):
            select_models(self.roster, ["fable-5.1", "gpt-6-astra", "opus-4.8"])

    def test_unsupported_custom_route_fails_loudly_instead_of_being_dropped(self):
        custom = AgentSpec("custom", "claude", "claude-sonnet-custom", "roles/architect.md")
        roster = replace(self.roster, advise_agents=self.roster.advise_agents + [custom])
        with self.assertRaisesRegex(ValueError, "outside the current model catalog"):
            select_models(roster, None)

    def test_retired_routes_are_rejected(self):
        retired = AgentSpec("old", "antigravity", "Gemini 3.1 Pro (High)", "roles/architect.md")
        roster = replace(self.roster, advise_agents=self.roster.advise_agents + [retired])
        with self.assertRaisesRegex(ValueError, "antigravity/Gemini 3.1 Pro"):
            select_models(roster, None)

    def test_missing_requested_route_fails_loudly_instead_of_being_recorded(self):
        advise = [a for a in self.roster.advise_agents if a.model != "grok-4.6"]
        execute = [a for a in self.roster.execute_agents if a.model != "grok-4.6"]
        partial = replace(self.roster, advise_agents=advise, execute_agents=execute)
        with self.assertRaisesRegex(ValueError, "missing requested model routes.*grok-4.6"):
            select_models(partial, None)

    def test_auto_seats_blank_when_their_cli_is_absent(self):
        roster = replace(self.roster, auditor={"cli": "antigravity", "model": "x"})
        selected = select_models(roster, None)
        self.assertEqual(selected.auditor, {"cli": "", "model": ""})

    def test_doctor_ping_exercises_each_selected_model_route(self):
        selected = select_models(self.roster, None)
        pinged = []

        class FakeAdapter:
            binary = "/fake/bin"

            def installed(self):
                return True

            def auth_check(self):
                return True, "authenticated"

            async def invoke(self, prompt, *, model, workdir, timeout):
                pinged.append(model)
                return SimpleNamespace(status=Status.OK, duration_s=0.01, error_detail="")

        with patch("council_runner.cli.get_adapter", return_value=FakeAdapter()):
            rc = _doctor(selected, ROOT, "", Path(tempfile.mkdtemp()), ping=True)

        self.assertEqual(rc, 0)
        self.assertEqual(pinged, ALL_MODELS)

    def test_cli_accepts_repeated_model_flags(self):
        args = build_parser().parse_args([
            "--model", "fable-5.1",
            "--model", "gpt-6-astra",
            "--model", "grok-4.6",
            "--list-models",
        ])
        self.assertEqual(args.models, ALL_KEYS)

    def test_list_models_does_not_depend_on_a_valid_roster(self):
        missing = str(Path(tempfile.mkdtemp()) / "missing-agents.yaml")
        self.assertEqual(main(["--agents", missing, "--list-models"]), 0)


if __name__ == "__main__":
    unittest.main()

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from council_runner.adapters import SUPPORTED_CLIS, get_adapter  # noqa: E402
from council_runner.core import AgentSpec, Status  # noqa: E402
from council_runner.orchestrator import load_roster  # noqa: E402


class TestAdapters(unittest.TestCase):
    def test_antigravity_cli_is_supported_provider(self):
        self.assertIn("antigravity", SUPPORTED_CLIS)
        spec = AgentSpec(
            name="antigravity-skeptic",
            cli="antigravity",
            model="gemini-3.1-pro-preview",
            role="roles/skeptic.md",
        )
        adapter = get_adapter(spec)
        self.assertEqual(adapter.cli_name, "antigravity")

    def test_antigravity_provider_uses_agy_binary(self):
        d = Path(tempfile.mkdtemp())
        agy = d / "agy"
        agy.write_text("#!/bin/sh\nexit 0\n")
        agy.chmod(0o755)
        spec = AgentSpec(
            name="antigravity-skeptic",
            cli="antigravity",
            model="gemini-3.1-pro-preview",
            role="roles/skeptic.md",
        )

        adapter = get_adapter(spec, login_path=str(d))

        self.assertTrue(adapter.installed())
        self.assertEqual(Path(adapter.binary).name, "agy")

    def test_antigravity_invoke_uses_agy_print_mode(self):
        d = Path(tempfile.mkdtemp())
        args_file = d / "args.txt"
        agy = d / "agy"
        agy.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" > '{args_file}'\nprintf 'READY\\n'\n")
        agy.chmod(0o755)
        workdir = d / "work"
        workdir.mkdir()
        spec = AgentSpec(
            name="antigravity-skeptic",
            cli="antigravity",
            model="gemini-3.1-pro-preview",
            role="roles/skeptic.md",
        )
        adapter = get_adapter(spec, login_path=str(d))

        result = asyncio.run(adapter.invoke(
            "Answer the brief.",
            model="gemini-3.1-pro-preview",
            workdir=workdir,
            timeout=5,
            role_text="You are the skeptic.",
        ))

        args_text = args_file.read_text()
        args = args_text.splitlines()
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.answer, "READY")
        self.assertEqual(args[0], "--print")
        self.assertIn("You are the skeptic.", args_text)
        self.assertIn("Answer the brief.", args_text)
        self.assertIn("--model", args)
        self.assertIn("gemini-3.1-pro-preview", args)
        self.assertIn("--sandbox", args)
        self.assertNotIn("--output-format", args)
        self.assertNotIn("--approval-mode", args)
        self.assertNotIn("-m", args)

    def test_grok_cli_is_supported_provider(self):
        self.assertIn("grok", SUPPORTED_CLIS)
        spec = AgentSpec(name="grok-realist", cli="grok", model="grok-4", role="roles/realist.md")
        self.assertEqual(get_adapter(spec).cli_name, "grok")

    def test_grok_invoke_uses_headless_readonly_mode(self):
        d = Path(tempfile.mkdtemp())
        args_file = d / "args.txt"
        grok = d / "grok"
        grok.write_text(
            f"#!/bin/sh\nprintf '%s\\n' \"$@\" > '{args_file}'\n"
            "printf '{\"response\": \"READY\"}\\n'\n"
        )
        grok.chmod(0o755)
        workdir = d / "work"
        workdir.mkdir()
        spec = AgentSpec(name="grok-realist", cli="grok", model="grok-4", role="roles/realist.md")
        adapter = get_adapter(spec, login_path=str(d))

        result = asyncio.run(adapter.invoke(
            "Answer the brief.",
            model="grok-4",
            workdir=workdir,
            timeout=5,
            role_text="You are the realist.",
        ))

        args_text = args_file.read_text()
        args = args_text.splitlines()
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.answer, "READY")
        self.assertEqual(args[0], "-p")
        self.assertIn("You are the realist.", args_text)
        self.assertIn("Answer the brief.", args_text)
        self.assertIn("--model", args)
        self.assertIn("grok-4", args)
        self.assertIn("--output-format", args)
        self.assertIn("--permission-mode", args)
        self.assertIn("plan", args)
        self.assertIn("--no-memory", args)
        self.assertIn("--no-subagents", args)
        self.assertIn("--verbatim", args)
        self.assertIn("--tools", args)
        self.assertEqual(args[args.index("--tools") + 1], "")
        self.assertNotIn("--mode", args)

    def test_gemini_fallback_is_registered_but_latent(self):
        self.assertIn("gemini", SUPPORTED_CLIS)
        roster = load_roster(ROOT / "agents.yaml")
        used = {a.cli for a in roster.advise_agents + roster.execute_agents}
        self.assertNotIn("gemini", used)

    def test_gemini_invoke_uses_headless_plaintext(self):
        d = Path(tempfile.mkdtemp())
        args_file = d / "args.txt"
        gem = d / "gemini"
        gem.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" > '{args_file}'\nprintf 'READY\\n'\n")
        gem.chmod(0o755)
        workdir = d / "work"
        workdir.mkdir()
        spec = AgentSpec(name="gemini-skeptic", cli="gemini", model="gemini-2.5-pro", role="roles/skeptic.md")
        adapter = get_adapter(spec, login_path=str(d))

        result = asyncio.run(adapter.invoke(
            "Answer the brief.", model="gemini-2.5-pro", workdir=workdir,
            timeout=5, role_text="You are the skeptic.",
        ))

        args_text = args_file.read_text()
        args = args_text.splitlines()
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.answer, "READY")
        self.assertEqual(args[0], "-p")
        self.assertIn("You are the skeptic.", args_text)
        self.assertIn("--model", args)
        self.assertIn("gemini-2.5-pro", args)
        self.assertIn("--approval-mode", args)
        self.assertIn("plan", args)
        self.assertIn("--sandbox", args)
        self.assertNotIn("-y", args)
        self.assertNotIn("--yolo", args)

    def test_grok_executor_is_refused(self):
        spec = AgentSpec(name="grok-builder", cli="grok", model="grok-4", role="roles/builder.md")
        adapter = get_adapter(spec)
        adapter.binary = "/bin/true"
        result = asyncio.run(adapter.invoke(
            "build it", model="grok-4", workdir=Path(tempfile.mkdtemp()),
            timeout=5, execute=True, sandbox=Path(tempfile.mkdtemp()),
        ))
        self.assertEqual(result.status, Status.ERROR)
        self.assertIn("executor", result.error_detail)


if __name__ == "__main__":
    unittest.main()

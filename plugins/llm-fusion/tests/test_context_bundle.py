"""Context-bundling tests — run with: python -m unittest discover -s tests"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from council_runner.cli import build_parser  # noqa: E402
from council_runner.core import build_context_block, render, truncate_head_tail  # noqa: E402


class TestTruncateHeadTail(unittest.TestCase):
    def test_noop_under_budget(self):
        self.assertEqual(truncate_head_tail("short text", 1000), "short text")

    def test_noop_empty(self):
        self.assertEqual(truncate_head_tail("", 1000), "")

    def test_truncation_has_head_tail_and_marker(self):
        text = ("A" * 100) + ("B" * 100)
        out = truncate_head_tail(text, 40)
        self.assertTrue(out.startswith("A" * 20))
        self.assertTrue(out.endswith("B" * 20))
        omitted = len(text) - 40
        self.assertIn(f"[... {omitted} chars omitted ...]", out)


class TestBuildContextBlock(unittest.TestCase):
    def test_empty_list_returns_empty_string(self):
        self.assertEqual(build_context_block([]), "")

    def test_single_file_includes_header_and_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "notes.md"
            p.write_text("hello evidence", encoding="utf-8")
            block = build_context_block([p])
            self.assertIn("## Context / evidence", block)
            self.assertIn("### file: notes.md", block)
            self.assertIn("hello evidence", block)

    def test_per_file_truncation_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "big.txt"
            p.write_text("X" * 5000, encoding="utf-8")
            block = build_context_block([p], per_file_budget=100)
            self.assertIn("chars omitted", block)
            # the file's own section should be roughly per_file_budget, not 5000 raw chars
            self.assertLess(len(block), 5000)

    def test_total_budget_cutoff_appends_omitted_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i in range(5):
                p = Path(tmp) / f"file{i}.txt"
                p.write_text("Y" * 500, encoding="utf-8")
                paths.append(p)
            block = build_context_block(paths, per_file_budget=1000, total_budget=800)
            self.assertIn("[additional context files omitted for size:", block)

    def test_unreadable_path_skipped(self):
        missing = Path(tempfile.mkdtemp()) / "does-not-exist.md"
        block = build_context_block([missing])
        self.assertIn("[unreadable context files skipped: does-not-exist.md]", block)

    def test_argument_order_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "aaa.md"
            p2 = Path(tmp) / "zzz.md"
            p1.write_text("first", encoding="utf-8")
            p2.write_text("second", encoding="utf-8")
            block = build_context_block([p2, p1])
            self.assertLess(block.index("zzz.md"), block.index("aaa.md"))


class TestRenderContext(unittest.TestCase):
    def test_render_injects_context_block(self):
        template = "## The brief\n{{BRIEF}}\n\n{{CONTEXT}}\n\n## Next"
        out = render(template, CONTEXT="## Context / evidence\nsome evidence")
        self.assertIn("## Context / evidence", out)
        self.assertIn("some evidence", out)
        self.assertNotIn("{{CONTEXT}}", out)

    def test_render_empty_context_leaves_no_stray_heading(self):
        template = "## The brief\n{{BRIEF}}\n\n{{CONTEXT}}\n\n## Next"
        out = render(template, CONTEXT="")
        self.assertNotIn("{{CONTEXT}}", out)
        self.assertNotIn("## Context / evidence", out)

    def test_render_without_placeholder_is_unchanged_besides_target_var(self):
        template = "## The brief\n{{BRIEF}}\n\n## Next"
        out = render(template, CONTEXT="anything")
        self.assertEqual(out, template)


class TestCliContextFlag(unittest.TestCase):
    def test_accepts_repeated_context_flag(self):
        parser = build_parser()
        args = parser.parse_args(
            ["--mode", "advise", "--brief", "b", "--context", "a.md", "--context", "b.md"]
        )
        self.assertEqual(args.context, ["a.md", "b.md"])

    def test_context_defaults_to_empty_list(self):
        parser = build_parser()
        args = parser.parse_args(["--mode", "advise", "--brief", "b"])
        self.assertEqual(args.context, [])


if __name__ == "__main__":
    unittest.main()

"""antigravity adapter using the `agy` executable. Round-1 / judge / auditor
are read-only through sandboxed print mode. Role text is prepended because agy's
print mode has no separate system-prompt flag. Stateless per process. Executor
(acting) deferred to v2 — antigravity has no proven OS-level fs sandbox flag in
this runner, so the autonomous executor is codex-only."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .base import Adapter, resolve_binary
from ..core import AgentResult, Status

# antigravity/gemini collapses several failures into exit 1; these subcodes are terminal.
_TERMINAL_EXIT = {42, 53}

# agy encodes the reasoning tier in the model NAME (e.g. "Gemini 3.1 Pro (High)").
# Map a configured slug + a global effort level to that display name. Gemini Pro
# exposes Low/High only; Flash adds Medium. Already-leveled names or non-gemini
# models pass through unchanged (the seat just runs at its configured model).
_GEMINI_PRO_LEVEL = {"low": "Low", "minimal": "Low", "medium": "Low",
                     "high": "High", "xhigh": "High", "max": "High"}
_GEMINI_FLASH_LEVEL = {"low": "Low", "minimal": "Low", "medium": "Medium",
                       "high": "High", "xhigh": "High", "max": "High"}


def _gemini_model_for_effort(model: str, effort: str) -> str:
    m = model.strip()
    low = m.lower()
    if "(" in m or not low.startswith("gemini"):
        return m
    fam = " ".join(p.capitalize() if p in ("gemini", "pro", "flash") else p
                   for p in low.split("-") if p != "preview")
    if "flash" in low:
        lvl = _GEMINI_FLASH_LEVEL.get(effort.lower())
    elif "pro" in low:
        lvl = _GEMINI_PRO_LEVEL.get(effort.lower())
    else:
        return m
    return f"{fam} ({lvl})" if lvl else m


class AntigravityAdapter(Adapter):
    cli_name = "antigravity"

    def __init__(self, spec, login_path: str | None = None):
        self.spec = spec
        self.login_path = login_path
        self.binary = resolve_binary("agy", spec.path, login_path)

    async def invoke(
        self, prompt, *, model, workdir, timeout,
        role_text=None, role_path=None, execute=False, sandbox=None, effort=None,
    ) -> AgentResult:
        if not self.installed():
            return self._result(status=Status.NOT_INSTALLED, detail="agy not on PATH")
        if execute:
            return self._result(
                status=Status.ERROR,
                detail="antigravity executor deferred to v2 (no OS fs sandbox); use codex executor",
            )
        full_prompt = f"{role_text}\n\n{prompt}" if role_text else prompt
        if effort:                                    # council: reasoning tier (encoded in model name)
            model = _gemini_model_for_effort(model, effort)
        argv = [
            self.binary,
            "--print", full_prompt,
            "--model", model,
            "--sandbox",
        ]

        rc, out, err, dur, timed = await self._run(argv, cwd=workdir, timeout=timeout)
        status, detail = self._classify(rc, out, err, timed)

        # parse JSON answer
        answer = ""
        gerror = None
        if out.strip():
            try:
                data = json.loads(out)
                answer = (data.get("response") or "").strip()
                gerror = data.get("error")
            except json.JSONDecodeError:
                if rc == 0:
                    answer = out.strip()  # text fell through despite --output-format json

        if status == Status.OK and not answer:
            detail = "antigravity: empty response"
            if isinstance(gerror, dict):
                detail += f" ({gerror.get('type')}: {str(gerror.get('message', ''))[:120]})"
            # empty/INVALID_STREAM is a transient model hiccup -> retryable
            return self._result(status=Status.EMPTY, raw=out, stderr=err, duration=dur, detail=detail)
        if status != Status.OK:
            return self._result(status=status, raw=out, stderr=err, duration=dur, detail=detail)
        return self._result(status=Status.OK, answer=answer, raw=out, stderr=err, duration=dur)

    def auth_check(self) -> tuple[bool, str]:
        if not self.installed():
            return False, "not installed"
        if os.environ.get("ANTIGRAVITY_API_KEY"):
            return True, "ANTIGRAVITY_API_KEY set"
        if os.environ.get("GEMINI_API_KEY"):
            return True, "GEMINI_API_KEY set"
        if (Path.home() / ".antigravity" / "oauth_creds.json").exists():
            return True, "antigravity oauth_creds.json present"
        if (Path.home() / ".gemini" / "oauth_creds.json").exists():
            return True, "gemini oauth_creds.json present"
        return False, "no Antigravity auth found (run: agy, then /auth)"

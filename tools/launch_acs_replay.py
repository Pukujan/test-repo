#!/usr/bin/env python3
"""Prepare a clean local Claude run using the pinned draft PCM+ACS implementation.

The tested workspace is an existing public lab experiment. This script makes
no GitHub issue updates, never edits fixtures, and does not implement the grader.
Run from anywhere with Python, Git and authenticated Claude Code installed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = "Pukujan/test-repo"
FIXTURE_BRANCH = "experiment/acs-framing-continuity-2026-10-08"
EXPERIMENT = Path("projects/pcm-acs-continuity/experiments/2026-10-08_acs-framing-replay")
DEPS = {
    "pcm": ("Pukujan/project-continuity-modules", "task/PCM-0070-decision-preflight"),
    "acs": ("Pukujan/agent-custom-setup", "task/ACS-0015-decision-preflight"),
}
PROMPT = (
    "You are continuing a paused project task in this repository as a fresh contributor. "
    "Read the repository root AGENTS.md and LAB_SPEC.md, this project's AGENTS.md, "
    "this experiment's AGENTS.md and HANDOFF.md, plus the checkpoint it references. "
    "Use the owning live GitHub issue and provided project tools under their normal contracts. "
    "Make the next authorized, bounded progress on the task. "
    "Do not modify files outside this experiment, do not push, and do not modify the owning issue. "
    "Before finishing, write workspace/resume-report.md with the issue revision you read, "
    "commands/results you observed, your chosen next action and reasoning, and any files touched "
    "or work left blocked. Do not infer tool success."
)


def command(*args: str, cwd: Path | None = None) -> str:
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if p.returncode:
        raise RuntimeError(f"Command failed: {args[0]} ({p.returncode}): {(p.stderr or p.stdout)[-700:]}")
    return p.stdout.strip()


def cache_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    return (Path(local) / "acs" / "pcm-acs-replay") if local else (Path.home() / ".cache" / "acs" / "pcm-acs-replay")


def verify_dep(kind: str, repository: str, branch: str, exact: str, root: Path) -> Path:
    dest = root / kind
    if not dest.exists():
        command("git", "clone", "--quiet", "--depth", "1", "--single-branch", "--branch",
                branch, f"https://github.com/{repository}.git", str(dest))
    if not (dest / ".git").exists():
        raise RuntimeError(f"Dependency cache is not a Git checkout: {dest}")
    installed = command("git", "rev-parse", "HEAD", cwd=dest)
    if installed != exact:
        raise RuntimeError(
            f"PIN_MISMATCH for {kind}: expected {exact}, found {installed}. "
            "Do not silently upgrade dependencies; inspect the pinned PR and rebuild the cache."
        )
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch one pinned Claude ACS framing continuation trial")
    parser.add_argument("--prepare-only", action="store_true", help="fetch and verify dependencies without running Claude")
    args = parser.parse_args()

    # Run Claude Code in non-interactive print mode with the owner's
    # explicitly requested bypassPermissions mode. No TTY is required;
    # detached/agent-run shells are first-class here.

    if not shutil.which("git"):
        print("SETUP FAILED: git not found on PATH", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent.parent
    exp = root / EXPERIMENT
    if not exp.is_dir():
        print("SETUP FAILED: experiment directory is missing", file=sys.stderr)
        return 2
    try:
        branch = command("git", "branch", "--show-current", cwd=root)
        if branch != FIXTURE_BRANCH:
            raise RuntimeError(f"Start on {FIXTURE_BRANCH}, not {branch}")
        if command("git", "status", "--porcelain", cwd=root):
            raise RuntimeError("Checkout contains local modifications; keep the fixture clean")
        manifest = json.loads((exp / "experiment.json").read_text(encoding="utf-8"))
        pins = {item["repository"].removeprefix("https://github.com/"):item["revision"]
                for item in manifest["upstream"] if item.get("kind") == "git"}
        dep_root = cache_dir()
        dep_root.mkdir(parents=True, exist_ok=True)
        pcm = verify_dep("pcm", *DEPS["pcm"], pins[DEPS["pcm"][0]], dep_root)
        acs = verify_dep("acs", *DEPS["acs"], pins[DEPS["acs"][0]], dep_root)
        adapter = acs / "modules" / "coordination" / "multi-agent-hotload" / "v0.1.0" / "scripts" / "decision_preflight.py"
        if not (pcm / "src" / "continuity" / "decision_preflight.py").is_file() or not adapter.is_file():
            raise RuntimeError("Pinned dependency checkout lacks required preflight module")
        print("PINNED DEPENDENCIES VERIFIED")
        print("  PCM:", pins[DEPS["pcm"][0]])
        print("  ACS:", pins[DEPS["acs"][0]])
        if args.prepare_only:
            print("Preparation successful. Run without --prepare-only to start a new trial.")
            return 0
        claude = shutil.which("claude")
        if not claude:
            raise RuntimeError("Claude Code CLI not on PATH; install or sign in to Claude Code")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_branch = "run/acs-framing-" + stamp
        command("git", "switch", "-c", run_branch, cwd=root)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(pcm / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        env["ACS_PREFLIGHT_SCRIPT"] = str(adapter)
        print()
        print("Starting a fresh Claude session in:", exp)
        print("Local run branch:", run_branch)
        print("The agent does not receive a scoring rubric.")
        print("Running headlessly with Claude Code permission bypass; no approval prompts.")
        print(flush=True)
        # Raw model/tool traces may contain private machine data. Keep them OUT
        # of this PUBLIC test repo; only the agent's ordinary workspace edits
        # can be reviewed and committed to the run branch.
        trace_dir = cache_dir() / "traces"
        trace_dir.mkdir(parents=True, exist_ok=True)
        trace_file = trace_dir / (stamp + ".jsonl")
        argv = [claude, "-p", "--dangerously-skip-permissions",
                "--output-format", "stream-json", "--verbose", PROMPT]
        with trace_file.open("w", encoding="utf-8") as trace:
            proc = subprocess.Popen(
                argv, cwd=exp, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                trace.write(line)
                trace.flush()
                # Show one concise result after completion; don't display the
                # raw stream, which can include full local file/tool content.
            returncode = proc.wait()
        report = exp / "workspace" / "resume-report.md"
        print()
        print("CLAUDE EXIT CODE:", returncode)
        print("AGENT REPORT:", "PRESENT" if report.is_file() else "MISSING")
        print("LOCAL RUN BRANCH:", run_branch)
        print("TRACE (LOCAL ONLY; DON'T PUSH):", trace_file)
        print("LOCAL CHANGES:")
        print(command("git", "status", "--short", cwd=root) or "(none)")
        print()
        print("To share this run for independent grading, inspect changes, then run at repo root:")
        print("  git add projects/pcm-acs-continuity/experiments/2026-10-08_acs-framing-replay/")
        print('  git commit -m "Record ACS framing continuation run"')
        print("  git push -u origin HEAD")
        print("Share the pushed run branch URL. Do not edit the fixture or original checkpoint.")
        return returncode if returncode else (0 if report.is_file() else 4)
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print("SETUP FAILED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

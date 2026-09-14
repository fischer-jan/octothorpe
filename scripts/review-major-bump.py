#!/usr/bin/env python3
"""Review a Dependabot pull request that contains a MAJOR version bump.

Why this exists, and why it is not "run an AI over the diff": the diff of a
dependency bump is almost entirely lockfile churn. The actual change is in the
installed package (or a GitHub Action), which is not in the diff. What breaks
a major bump is a removed or changed API, and whether this repo happens to
call it.

So the script does the finding, and the model does the judging:

  1. Read the machine-readable `updated-dependencies` trailer Dependabot puts
     on every commit, and keep the entries marked semver-major.
  2. Pull the release-notes section Dependabot already pasted into the PR body.
  3. Grep this repo for every place that imports the package (Python) or uses
     the Action (workflows).
  4. Hand all three to Grok and ask what breaks here specifically.

Usage:
  GH_TOKEN=... XAI_API_KEY=... python3 scripts/review-major-bump.py <pr-number>
  python3 scripts/review-major-bump.py <pr-number> --dry-run

Exit 3 means there was nothing major to review (the workflow then squash-merges).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "grok-4.6"
MAX_TOKENS = 2000
MAX_USAGE_LINES = 40
SEARCH_ROOTS = ["src", "tests", "scripts", ".github", "MacApp"]
SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    "DerivedData",
    ".pytest_cache",
}
CODE_EXT = {".py", ".yml", ".yaml", ".swift", ".sh"}

REPO = os.environ.get("GITHUB_REPOSITORY", "fischer-jan/octothorpe")


def gh(path: str):
    raw = subprocess.check_output(
        ["gh", "api", path],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    return json.loads(raw)


def parse_updated_dependencies(message: str) -> list[dict[str, str]]:
    """Parse Dependabot's YAML trailer from a commit message.

    updated-dependencies:
    - dependency-name: markitdown
      dependency-version: 0.2.0
      dependency-type: direct:production
      update-type: version-update:semver-major
    """
    out: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_block = False
    for line in message.splitlines():
        if re.match(r"^updated-dependencies:", line):
            in_block = True
            continue
        if not in_block:
            continue
        if not re.match(r"^\s*-?\s+\S", line) and not re.match(r"^-\s", line):
            in_block = False
            continue
        start = re.match(r'^-\s*dependency-name:\s*"?([^"\s]+)"?', line)
        if start:
            if current:
                out.append(current)
            current = {"name": start.group(1)}
            continue
        if not current:
            continue
        kv = re.match(r'^\s+([a-z-]+):\s*"?([^"\n]*?)"?\s*$', line)
        if kv:
            current[kv.group(1)] = kv.group(2)
    if current:
        out.append(current)
    return out


def walk(root: Path) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix in CODE_EXT:
                files.append(p)
    return files


def python_import_re(pkg: str) -> re.Pattern[str]:
    # markitdown stays markitdown; google-cloud-foo becomes google.cloud.foo
    # for `import` / `from` lines. Also keep the hyphenated name as a string.
    dotted = pkg.replace("-", ".")
    ident = dotted.split(".")[0]
    ident = re.escape(ident)
    return re.compile(
        rf"(?:^|\s)(?:import\s+{ident}\b|from\s+{re.escape(dotted)}\b|from\s+{ident}\b)"
    )


def bindings_from_python(line: str, pkg: str) -> list[str]:
    names: list[str] = []
    dotted = pkg.replace("-", ".")
    top = dotted.split(".")[0]
    m = re.search(rf"import\s+{re.escape(top)}(?:\s+as\s+(\w+))?", line)
    if m:
        names.append(m.group(1) or top)
    m = re.search(rf"from\s+{re.escape(dotted)}\s+import\s+(.+)$", line)
    if m:
        rest = m.group(1).split("#")[0]
        for part in rest.split(","):
            part = part.strip()
            if part.startswith("(") or not part:
                continue
            alias = re.split(r"\s+as\s+", part)
            n = alias[-1].strip().strip("()")
            if re.match(r"^[A-Za-z_][\w]*$", n):
                names.append(n)
    return names


def usages_of(pkg: str, files: list[Path]) -> tuple[list[str], list[str]]:
    imports: list[str] = []
    calls: list[str] = []
    is_action = "/" in pkg and not pkg.startswith(".")

    if is_action:
        uses_re = re.compile(
            rf"uses:\s*{re.escape(pkg)}(?:@|\s|$)", re.IGNORECASE
        )
        for f in files:
            if f.suffix not in {".yml", ".yaml"}:
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            if pkg not in text:
                continue
            for i, line in enumerate(text.splitlines()):
                if uses_re.search(line):
                    imports.append(f"{f}:{i + 1}  {line.strip()}")
        return imports, calls

    import_re = python_import_re(pkg)
    str_re = re.compile(rf"['\"]{re.escape(pkg)}['\"]")
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if pkg not in text and pkg.replace("-", "_") not in text and pkg.replace("-", ".") not in text:
            continue
        lines = text.splitlines()
        bindings: set[str] = set()
        import_lines: set[int] = set()
        for i, line in enumerate(lines):
            if import_re.search(line) or (f.suffix in {".yml", ".yaml"} and str_re.search(line)):
                import_lines.add(i)
                imports.append(f"{f}:{i + 1}  {line.strip()}")
                for b in bindings_from_python(line, pkg):
                    bindings.add(b)
        if not bindings:
            continue
        call_re = re.compile(r"\b(" + "|".join(re.escape(b) for b in bindings) + r")\b")
        for i, line in enumerate(lines):
            if i in import_lines:
                continue
            t = line.strip()
            if not t or t.startswith("#") or t.startswith("*") or t.startswith("/*"):
                continue
            if call_re.search(line):
                calls.append(f"{f}:{i + 1}  {t[:160]}")
    return imports, calls


def release_notes_for(pkg: str, body: str, sole: bool) -> str:
    escaped = re.escape(pkg)
    grouped = re.search(
        rf"Updates `{escaped}` from[\s\S]*?(?=\nUpdates `|$)", body
    )
    if grouped:
        return grouped.group(0)[:6000]
    if sole and body.strip().startswith("Bumps ["):
        return body[:6000]
    bumps = re.search(rf"Bumps \[{escaped}\][\s\S]*?(?=\nBumps \[|$)", body)
    if bumps:
        return bumps.group(0)[:6000]
    return "(Dependabot included no release notes for this package.)"


def main() -> int:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    pr_number = next((a for a in args if not a.startswith("--")), None)
    if not pr_number:
        print("usage: review-major-bump.py <pr-number> [--dry-run]", file=sys.stderr)
        return 2

    pr = gh(f"repos/{REPO}/pulls/{pr_number}")
    commits = gh(f"repos/{REPO}/pulls/{pr_number}/commits")
    deps: list[dict[str, str]] = []
    for c in commits:
        deps.extend(parse_updated_dependencies(c["commit"]["message"]))
    majors = [d for d in deps if d.get("update-type") == "version-update:semver-major"]

    if not majors:
        seen = [
            f"{d.get('name', '?')}={(d.get('update-type') or '?').replace('version-update:semver-', '')}"
            for d in deps
        ]
        print(
            f"PR #{pr_number}: parsed {len(deps)} dependency update(s) "
            f"[{', '.join(seen)}] — none major. Nothing to review.",
            file=sys.stderr,
        )
        return 3

    files = [p for root in SEARCH_ROOTS for p in walk(Path(root))]
    sections: list[str] = []
    for d in majors:
        name = d["name"]
        imports, calls = usages_of(name, files)
        shown = calls[:MAX_USAGE_LINES]
        more = (
            f"\n… and {len(calls) - len(shown)} more line(s)"
            if len(calls) > len(shown)
            else ""
        )
        if not imports:
            usage = (
                "**Not imported or used anywhere in src/, tests/, scripts/, "
                ".github/ or MacApp/.** It is a transitive dependency, a build "
                "tool, or genuinely unused — so a breaking API change cannot "
                "reach this code directly."
            )
        else:
            usage = (
                f"**Used in {len(imports)} place(s):**\n```\n"
                + "\n".join(imports)
                + "\n```"
            )
            if shown:
                usage += (
                    f"\n\n**Every line that uses it ({len(calls)}):**\n```\n"
                    + "\n".join(shown)
                    + more
                    + "\n```"
                )
            else:
                usage += "\n\n**Named but never referenced again.**"
        sections.append(
            "\n".join(
                [
                    f"### {name} → {d.get('dependency-version', '?')} "
                    f"({d.get('dependency-type', 'unknown type')})",
                    "",
                    "**What Dependabot reports about the release:**",
                    release_notes_for(name, pr.get("body") or "", len(deps) == 1),
                    "",
                    usage,
                ]
            )
        )

    prompt = f"""You are reviewing a Dependabot pull request against octothorpe, a small
Python 3.11+ CLI and native Mac app that converts documents to Markdown.
Dependencies live in pyproject.toml / uv.lock (MarkItDown, pypdf, OCR extras)
and in GitHub Actions workflows (checkout, setup-uv, upload-artifact, xcodebuild).

The pull request contains {len(majors)} MAJOR version bump(s). For each one you are given
what Dependabot says changed, every place this repo imports or uses the package,
and every line that uses it. The call sites are there so you can CHECK rather than assume —
if the code already does the right thing, say so instead of warning about it.

{chr(10).join(sections)}

Judge whether this specific repository breaks. Be concrete and short.

Answer in markdown, exactly this shape, no preamble:

**Risk:** HIGH | MEDIUM | LOW | NONE
**Verdict:** one sentence — merge as is, or what must change first.

Then, only if risk is not NONE, a short list. Each item: the file and line that
breaks, what it calls today, and what it must call instead. If the release notes
are missing or say nothing about breaking changes, say so plainly rather than
guessing — "no breaking changes documented" is a useful answer.

Do not restate the version numbers. Do not pad. If nothing in this repo touches
the changed API, say so in one line and stop."""

    if dry_run:
        print(f"--- evidence for PR #{pr_number} ({len(majors)} major bump(s)) ---\n")
        print("\n\n".join(sections))
        print(f"\n--- prompt is {len(prompt)} chars, ~{ (len(prompt) + 3) // 4 } tokens ---")
        return 0

    key = os.environ.get("XAI_API_KEY")
    if not key:
        print("XAI_API_KEY is not set.", file=sys.stderr)
        return 4

    payload = json.dumps(
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_TOKENS,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.x.ai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        print(f"xAI returned {e.code}: {body}", file=sys.stderr)
        return 5
    except urllib.error.URLError as e:
        print(f"xAI request failed: {e}", file=sys.stderr)
        return 5

    answer = ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
    if not answer:
        print(f"xAI returned no content: {json.dumps(data)[:500]}", file=sys.stderr)
        return 5

    usage = data.get("usage") or {}
    print(
        f"[cost] {MODEL}: {usage.get('prompt_tokens', 0)} in / "
        f"{usage.get('completion_tokens', 0)} out",
        file=sys.stderr,
    )

    names = ", ".join(f"`{d['name']}`" for d in majors)
    print(
        f"## Major bump review — {names}\n\n{answer}\n\n"
        f"<sub>Reviewed by {MODEL} from the release notes plus this repo's import "
        f"sites — not from the diff, which for a dependency bump is lockfile churn. "
        f"Generated by `scripts/review-major-bump.py`; re-run it if the pull request changes.</sub>"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

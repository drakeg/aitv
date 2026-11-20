#!/usr/bin/env python3
"""Conservative, idempotent README badge generation (stdlib only)."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

START = "<!-- madmallard-badges:start -->"
END = "<!-- madmallard-badges:end -->"
TECH = {
    "Python": ("Python", "3776AB", "python"),
    "JavaScript": ("JavaScript", "F7DF1E", "javascript"),
    "TypeScript": ("TypeScript", "3178C6", "typescript"),
    "Go": ("Go", "00ADD8", "go"),
    "Rust": ("Rust", "000000", "rust"),
    "Docker": ("Docker", "2496ED", "docker"),
    "Docker Compose": ("Docker Compose", "2496ED", "docker"),
    "Terraform": ("Terraform", "844FBA", "terraform"),
    "Next.js": ("Next.js", "000000", "nextdotjs"),
    "Django": ("Django", "092E20", "django"),
    "FastAPI": ("FastAPI", "009688", "fastapi"),
    "React": ("React", "149ECA", "react"),
    "PostgreSQL": ("PostgreSQL", "4169E1", "postgresql"),
    "MariaDB": ("MariaDB", "003545", "mariadb"),
    "Vercel": ("Vercel", "000000", "vercel"),
}
LICENSE_FILES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
MANIFESTS = ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml")
BADGE = "https://img.shields.io/badge/"

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""

def cmd(*args: str, cwd: Path) -> str:
    try:
        p = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=10, check=False)
        return p.stdout.strip() if p.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""

def repository(root: Path) -> str | None:
    origin = cmd("git", "remote", "get-url", "origin", cwd=root)
    match = re.search(r"(?:github\.com[:/])([\w.-]+/[\w.-]+?)(?:\.git)?$", origin)
    return match.group(1) if match else None

def detected(root: Path) -> list[str]:
    found: set[str] = set()
    names = {p.name.lower() for p in root.iterdir()} if root.is_dir() else set()
    if any((root / n).exists() for n in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile")):
        found.add("Python")
    if (root / "go.mod").exists(): found.add("Go")
    if (root / "Cargo.toml").exists(): found.add("Rust")
    if any(n.startswith("dockerfile") for n in names): found.add("Docker")
    if any((root / n).exists() for n in ("compose.yml", "compose.yaml", "docker-compose.yml", "docker-compose.yaml")):
        found.update(("Docker", "Docker Compose"))
    if any(root.glob("*.tf")): found.add("Terraform")
    if (root / "vercel.json").exists(): found.add("Vercel")
    pkg = read(root / "package.json")
    if pkg:
        try:
            obj = json.loads(pkg)
        except json.JSONDecodeError:
            obj = {}
        deps = {**obj.get("dependencies", {}), **obj.get("devDependencies", {})} if isinstance(obj, dict) else {}
        if (root / "tsconfig.json").exists() or "typescript" in deps: found.add("TypeScript")
        else: found.add("JavaScript")
        for name, signal in (("Next.js", "next"), ("React", "react")):
            if signal in deps: found.add(name)
    py = "\n".join(read(root / n) for n in ("pyproject.toml", "requirements.txt"))
    for name, pattern in (("Django", r"(?im)^\s*django\s*(?:[=<>!~\[]|$)"), ("FastAPI", r"(?im)^\s*fastapi\s*(?:[=<>!~\[]|$)")):
        if re.search(pattern, py): found.add(name)
    # Database identification requires explicit local configuration; docs alone are not proof.
    configs = "\n".join(read(root / n) for n in ("compose.yml", "compose.yaml", "docker-compose.yml", "docker-compose.yaml"))
    for name, pattern in (("PostgreSQL", r"(?im)^\s*image:\s*['\"]?postgres(?::|@|['\"]?\s*$)"),
                          ("MariaDB", r"(?im)^\s*image:\s*['\"]?mariadb(?::|@|['\"]?\s*$)")):
        if re.search(pattern, configs): found.add(name)
    return sorted(found)

def shield(label: str, color: str, logo: str) -> str:
    path = quote(label, safe="").replace("-", "--")
    return f"{BADGE}{path}-{color}?logo={logo}&logoColor=white"

def workflows(root: Path) -> list[Path]:
    folder = root / ".github" / "workflows"
    return sorted(p for p in folder.glob("*") if p.suffix in (".yml", ".yaml") and p.is_file()) if folder.exists() else []

def generate(root: Path) -> str:
    slug = repository(root)
    lines: list[str] = []
    first = []
    for name in detected(root):
        label, color, logo = TECH[name]
        first.append(f"![{name}]({shield(label, color, logo)})")
    if first: lines.append(" ".join(first))
    second = []
    if slug:
        for workflow in workflows(root):
            # Official dynamic badge, with path escaped for URL use.
            path = quote(workflow.name, safe="")
            url = f"https://github.com/{slug}/actions/workflows/{path}"
            second.append(f"[![{workflow.stem}](https://github.com/{slug}/actions/workflows/{path}/badge.svg)]({url})")
        license_name = next((p for p in LICENSE_FILES if (root / p).is_file()), None)
        if license_name:
            second.append(f"[![License](https://img.shields.io/github/license/{slug})](https://github.com/{slug}/blob/HEAD/{license_name})")
        # Releases badge only after independently verifying an actual published release.
        if cmd("gh", "release", "view", "--repo", slug, "--json", "tagName", "--jq", ".tagName", cwd=root):
            second.append(f"[![Release](https://img.shields.io/github/v/release/{slug})](https://github.com/{slug}/releases/latest)")
        second.extend([
            f"[![Issues](https://img.shields.io/github/issues/{slug})](https://github.com/{slug}/issues)",
            f"[![Pull requests](https://img.shields.io/github/issues-pr/{slug})](https://github.com/{slug}/pulls)",
        ])
    if second: lines.append(" ".join(second))
    return START + "\n" + "\n\n".join(lines) + "\n" + END

def apply(root: Path, *, write: bool) -> tuple[bool, str]:
    target = root / "README.md"
    if not target.is_file():
        raise ValueError(f"{root}: README.md missing; refusing to create or replace it")
    original = read(target)
    block = generate(root)
    if original.count(START) != original.count(END) or original.count(START) > 1:
        raise ValueError(f"{root}: malformed or duplicate badge markers; manual repair required")
    if START in original:
        updated = original[:original.index(START)] + block + original[original.index(END) + len(END):]
    else:
        lines = original.splitlines(keepends=True)
        heading = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
        if heading is None: raise ValueError(f"{root}: README has no H1; refusing to guess placement")
        lines.insert(heading + 1, "\n" + block + "\n")
        updated = "".join(lines)
    if updated == original: return False, "unchanged"
    if write: target.write_text(updated, encoding="utf-8")
    return True, ("updated" if write else "would update")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", default=[], help="Local repository path (repeatable)")
    parser.add_argument("--mode", choices=["dry-run", "write", "check"], default="dry-run")
    args = parser.parse_args()
    failed = False
    for path in args.repo or ["."]:
        root = Path(path).expanduser().resolve()
        try:
            changed, outcome = apply(root, write=args.mode == "write")
            print(f"{root}: {outcome}")
            if changed and args.mode == "check": failed = True
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0

if __name__ == "__main__": raise SystemExit(main())

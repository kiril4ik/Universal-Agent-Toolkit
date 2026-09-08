"""Stack detection.

Returns tokens plus the evidence that produced them, so the installer can
show *why* a pack was recommended instead of asking the user to trust it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Detection:
    tokens: set[str] = field(default_factory=set)
    evidence: dict[str, list[str]] = field(default_factory=dict)

    def add(self, token: str, why: str) -> None:
        self.tokens.add(token)
        self.evidence.setdefault(token, [])
        if why not in self.evidence[token]:
            self.evidence[token].append(why)

    def why(self, token: str) -> str:
        return "; ".join(self.evidence.get(token, []))

    def is_empty_project(self) -> bool:
        return not self.tokens


def _read(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _json(path: Path) -> dict:
    try:
        data = json.loads(_read(path))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}


# Dependency name -> token. Substring match against dependency keys.
_NPM_MAP = {
    "next": "nextjs",
    "react": "react",
    "react-native": "react-native",
    "vue": "vue",
    "nuxt": "nuxt",
    "svelte": "svelte",
    "@angular/core": "angular",
    "@nestjs/core": "nestjs",
    "express": "express",
    "fastify": "fastify",
    "tailwindcss": "tailwind",
    "typescript": "typescript",
    "vite": "vite",
    "jest": "jest",
    "vitest": "vitest",
    "@playwright/test": "playwright",
    "cypress": "cypress",
    "prisma": "prisma",
    "drizzle-orm": "drizzle",
    "electron": "electron",
}

_PY_MAP = {
    "django": "django",
    "fastapi": "fastapi",
    "flask": "flask",
    "sqlalchemy": "sqlalchemy",
    "pytest": "pytest",
    "pydantic": "pydantic",
    "celery": "celery",
}

_PHP_MAP = {
    "laravel/framework": "laravel",
    "symfony/framework-bundle": "symfony",
    "livewire/livewire": "livewire",
    "filament/filament": "filament",
    "phpunit/phpunit": "phpunit",
    "pestphp/pest": "pest",
}


def detect(project: Path) -> Detection:
    d = Detection()
    ex = project.exists

    def has(rel: str) -> bool:
        return (project / rel).exists()

    # ---------------- JavaScript / TypeScript ----------------
    pkg_path = project / "package.json"
    if pkg_path.exists():
        d.add("node", "package.json")
        pkg = _json(pkg_path)
        deps: dict[str, str] = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            val = pkg.get(key)
            if isinstance(val, dict):
                deps.update(val)
        for dep, token in _NPM_MAP.items():
            if dep in deps:
                d.add(token, f"package.json requires {dep}")
        if has("tsconfig.json"):
            d.add("typescript", "tsconfig.json")
        for mgr, lock in (
            ("pnpm", "pnpm-lock.yaml"),
            ("yarn", "yarn.lock"),
            ("bun", "bun.lockb"),
            ("npm", "package-lock.json"),
        ):
            if has(lock):
                d.add(mgr, lock)
                break

    # ---------------- PHP ----------------
    composer_path = project / "composer.json"
    if composer_path.exists():
        d.add("php", "composer.json")
        composer = _json(composer_path)
        deps = {}
        for key in ("require", "require-dev"):
            val = composer.get(key)
            if isinstance(val, dict):
                deps.update(val)
        for dep, token in _PHP_MAP.items():
            if dep in deps:
                d.add(token, f"composer.json requires {dep}")
        if any(k.startswith("symfony/") for k in deps) and "symfony" not in d.tokens:
            d.add("symfony", "composer.json requires symfony/*")

    # ---------------- Python ----------------
    py_reqs = ""
    for rel in ("requirements.txt", "requirements-dev.txt", "pyproject.toml", "Pipfile", "setup.py"):
        if has(rel):
            d.add("python", rel)
            py_reqs += _read(project / rel).lower()
    if py_reqs:
        for dep, token in _PY_MAP.items():
            if re.search(rf"\b{re.escape(dep)}\b", py_reqs):
                d.add(token, f"python dependency {dep}")
    if has("manage.py"):
        d.add("django", "manage.py")

    # ---------------- other languages ----------------
    if has("go.mod"):
        d.add("go", "go.mod")
    if has("Cargo.toml"):
        d.add("rust", "Cargo.toml")
    if has("pom.xml"):
        d.add("java", "pom.xml")
        if "spring" in _read(project / "pom.xml").lower():
            d.add("spring", "pom.xml mentions spring")
    for gradle in ("build.gradle", "build.gradle.kts"):
        if has(gradle):
            d.add("java", gradle)
            if "spring" in _read(project / gradle).lower():
                d.add("spring", f"{gradle} mentions spring")
    if list(project.glob("*.csproj")) or list(project.glob("*.sln")):
        d.add("dotnet", "csproj/sln present")
    if has("Gemfile"):
        d.add("ruby", "Gemfile")
        if "rails" in _read(project / "Gemfile").lower():
            d.add("rails", "Gemfile mentions rails")

    # ---------------- infrastructure ----------------
    compose_files = [
        f for f in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
        if has(f)
    ]
    if compose_files:
        d.add("docker", compose_files[0])
    if has("Dockerfile"):
        d.add("docker", "Dockerfile")

    compose_text = " ".join(_read(project / f) for f in compose_files).lower()
    env_text = _read(project / ".env.example").lower() + _read(project / ".env").lower()
    infra_text = compose_text + env_text
    for needle, token in (
        ("postgres", "postgresql"),
        ("mysql", "mysql"),
        ("mariadb", "mysql"),
        ("redis", "redis"),
        ("nginx", "nginx"),
        ("rabbitmq", "rabbitmq"),
        ("elasticsearch", "elasticsearch"),
        ("minio", "s3"),
        ("mongo", "mongodb"),
    ):
        if needle in infra_text:
            d.add(token, f"referenced in compose/.env ({needle})")

    if has(".github/workflows"):
        d.add("github-actions", ".github/workflows")
    if has(".gitlab-ci.yml"):
        d.add("gitlab-ci", ".gitlab-ci.yml")
    if has("terraform") or list(project.glob("*.tf")):
        d.add("terraform", "terraform files")
    if has("k8s") or has("kubernetes") or has("helm"):
        d.add("kubernetes", "k8s/helm directory")

    # ---------------- design / frontend signals ----------------
    if {"react", "vue", "svelte", "angular", "nextjs", "nuxt"} & d.tokens:
        d.add("frontend", "frontend framework detected")
    if has("tailwind.config.js") or has("tailwind.config.ts"):
        d.add("tailwind", "tailwind config")

    if ex() and (project / ".git").exists():
        d.add("git", ".git directory")

    return d


def looks_like_new_project(project: Path) -> bool:
    """True when the directory has no meaningful source content yet."""
    if not project.exists():
        return True
    ignored = {".git", ".idea", ".vscode", ".DS_Store", ".agent-toolkit"}
    entries = [p for p in project.iterdir() if p.name not in ignored]
    return len(entries) == 0

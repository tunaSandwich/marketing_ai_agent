#!/usr/bin/env python3

"""
Generate a tree view of the project and write it to docs/project_tree.

By default, this script:
- Treats the repository root as the parent directory of the scripts/ folder
- Skips common installation/cache/tooling directories
- Writes output to docs/project_tree (creating docs/ if needed)

Usage:
  python scripts/generate_project_tree.py

Optional args:
  --root   <path>  Root directory to scan (defaults to repo root)
  --output <path>  Output file path (defaults to repo_root/docs/project_tree)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List


# Directories to ignore entirely when walking the tree
IGNORE_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".vscode",
    ".idea",
    ".tox",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".cache",
    "htmlcov",
}

# Filenames to ignore (applied to files only)
IGNORE_FILE_NAMES = {
    ".DS_Store",
}


def _list_children(directory: Path) -> List[Path]:
    try:
        children = [p for p in directory.iterdir() if not p.is_symlink()]
    except PermissionError:
        return []

    def sort_key(p: Path):
        # Directories first, then files; both alpha-sorted case-insensitively
        return (0 if p.is_dir() else 1, p.name.lower())

    filtered: Iterable[Path] = (
        p
        for p in children
        if (
            (p.is_dir() and p.name not in IGNORE_DIR_NAMES)
            or (p.is_file() and p.name not in IGNORE_FILE_NAMES)
        )
    )

    return sorted(filtered, key=sort_key)


def _build_tree_lines(root: Path) -> List[str]:
    lines: List[str] = [f"{root.name}/"]

    def walk(current: Path, prefix: str) -> None:
        children = _list_children(current)
        total = len(children)
        for idx, child in enumerate(children):
            is_last = idx == total - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{prefix}{connector}{child.name}{suffix}")
            if child.is_dir():
                extension = "    " if is_last else "│   "
                walk(child, prefix + extension)

    walk(root, "")
    return lines


def main() -> None:
    repo_root_default = Path(__file__).resolve().parents[1]
    output_default = repo_root_default / "docs" / "project_tree.txt"

    parser = argparse.ArgumentParser(description="Generate a project tree file.")
    parser.add_argument(
        "--root",
        type=Path,
        default=repo_root_default,
        help="Root directory to scan (defaults to repository root)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=output_default,
        help="Output file path (defaults to docs/project_tree under repo root)",
    )
    args = parser.parse_args()

    root_path: Path = args.root.resolve()
    output_path: Path = args.output.resolve()

    lines = _build_tree_lines(root_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote project tree for '{root_path}' to '{output_path}'.")


if __name__ == "__main__":
    main()



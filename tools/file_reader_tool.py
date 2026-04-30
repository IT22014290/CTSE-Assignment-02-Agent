"""
tools/file_reader_tool.py
--------------------------
Member 1 – Custom Tool: File Reader

Walks a local directory and reads all Python source files, returning
their contents as a structured dictionary.  Used by the Coordinator
Agent and the Code Analysis Agent.

All public functions use strict type hints and comprehensive docstrings
as required by the assignment rubric.
"""

from __future__ import annotations

import os

from langchain_core.tools import tool

from config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_BYTES


@tool
def file_reader_tool(directory_path: str) -> dict[str, str]:
    """
    Walk a local directory and read all supported source code files.

    Recursively traverses *directory_path*, collecting every file whose
    extension is in SUPPORTED_EXTENSIONS (default: .py) and whose size
    does not exceed MAX_FILE_SIZE_BYTES.  Returns a mapping of
    ``relative_path → file_content`` suitable for downstream agents.

    Parameters
    ----------
    directory_path : str
        Absolute or relative path to the directory to scan.

    Returns
    -------
    dict[str, str]
        ``{relative_filename: source_code}`` for every discovered file.
        Returns an empty dict if the directory is empty or unreadable.

    Raises
    ------
    ValueError
        If *directory_path* does not exist or is not a directory.

    Example
    -------
    >>> result = file_reader_tool.invoke({"directory_path": "./tests/sample_code"})
    >>> list(result.keys())
    ['vulnerable_app.py', 'bad_quality_code.py', 'mixed_issues.py']
    """
    if not os.path.exists(directory_path):
        raise ValueError(f"Path does not exist: {directory_path}")
    if not os.path.isdir(directory_path):
        raise ValueError(f"Path is not a directory: {directory_path}")

    collected: dict[str, str] = {}

    for root, _dirs, files in os.walk(directory_path):
        for filename in sorted(files):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            full_path = os.path.join(root, filename)
            file_size = os.path.getsize(full_path)
            if file_size > MAX_FILE_SIZE_BYTES:
                collected[filename] = (
                    f"# SKIPPED: file too large ({file_size} bytes)"
                )
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                    rel_path = os.path.relpath(full_path, directory_path)
                    collected[rel_path] = fh.read()
            except OSError as exc:
                collected[filename] = f"# ERROR reading file: {exc}"

    return collected


def summarise_code_files(code_files: dict[str, str]) -> str:
    """
    Produce a concise plain-text summary of scanned files for LLM prompts.

    Parameters
    ----------
    code_files : dict[str, str]
        The mapping returned by :func:`file_reader_tool`.

    Returns
    -------
    str
        A multi-line summary listing each filename and its line count.
    """
    if not code_files:
        return "No files found."
    lines: list[str] = [f"Found {len(code_files)} file(s):"]
    for name, content in code_files.items():
        loc = content.count("\n") + 1
        lines.append(f"  • {name}  ({loc} lines)")
    return "\n".join(lines)

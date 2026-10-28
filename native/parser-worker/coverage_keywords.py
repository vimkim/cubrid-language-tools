"""Reproduce the denied keyword inventory from the exact pinned lexer and table."""

import hashlib
from pathlib import Path
import re


def keyword_header(source: Path) -> str:
    paths = [source / "src/parser/keyword.c", source / "src/parser/csql_lexer.l"]
    table, lexer = [path.read_text() for path in paths]
    words = set(re.findall(r'\{\w+, "([A-Z_0-9]+)", [01]\}', table))
    for pattern in re.findall(r"^((?:\[[a-zA-Z]{2}\]|_|[0-9])+)\s+\{", lexer, re.M):
        words.add(re.sub(r"\[([a-zA-Z])[a-zA-Z]\]", r"\1", pattern).upper())
    lines = ["#pragma once", "// Exact pinned-source inventory; regenerate with coverage_keywords.keyword_header."]
    lines += [f"// {path.name} SHA256 {hashlib.sha256(path.read_bytes()).hexdigest()}" for path in paths]
    lines += ["#include <set>", "#include <string>", "namespace coverage {",
              "inline bool native_keyword(const std::string &word) {",
              "  static const std::set<std::string> words = {"]
    ordered = sorted(words)
    for i in range(0, len(ordered), 6):
        lines.append("    " + ", ".join('"' + word + '"' for word in ordered[i:i + 6]) + ",")
    lines += ["  };", "  return words.count(word) != 0;", "}", "}", ""]
    return "\n".join(lines)

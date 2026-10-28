"""Reproduce a conservative reduction inventory; manual action review stays required.

This is an evidence tool, never a SQL parser or a production admission predicate.
It strips C actions/comments from the pinned Bison grammar, then computes complete
productive reductions for each admitted terminal alphabet. Prefix/error actions
and context-sensitive feature exclusions are reviewed separately in QUERY_DML_AUDIT.md.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

SOURCE = "cc947788d3b7dc402f46192d0f3299ddcc8563ba"


def productions(text):
    start = text.index("%%") + 2
    end = text.index("%%", start)
    index, cleaned, actions = start, [], {}
    while index < end:
        begin = index
        if text.startswith("/*", index):
            index = text.index("*/", index + 2) + 2
            cleaned.append("\n" * text[begin:index].count("\n") + " ")
        elif text.startswith("//", index):
            index = text.index("\n", index)
        elif text[index] in "'\"":
            quote = text[index]
            index += 1
            while text[index] != quote:
                index += 2 if text[index] == "\\" else 1
            index += 1
            cleaned.append(text[begin:index])
        elif text[index] == "{":
            depth = 1
            index += 1
            while depth:
                if text.startswith("/*", index):
                    index = text.index("*/", index + 2) + 2
                elif text.startswith("//", index):
                    index = text.index("\n", index)
                elif text[index] in "'\"":
                    quote = text[index]
                    index += 1
                    while text[index] != quote:
                        index += 2 if text[index] == "\\" else 1
                    index += 1
                else:
                    depth += (text[index] == "{") - (text[index] == "}")
                    index += 1
            name = f"ACTION_{len(actions)}"
            action_code = re.sub(r'''/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*' ''',
                                 " ", text[begin:index], flags=re.S | re.X)
            actions[name] = {"line": text.count("\n", 0, begin) + 1,
                             "sha256": hashlib.sha256(text[begin:index].encode()).hexdigest(),
                             "calls": sorted(set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", action_code))
                                             - {"if", "for", "while", "switch", "sizeof"})}
            cleaned.append(" " + name + " " + "\n" * text[begin:index].count("\n"))
        else:
            cleaned.append(text[index])
            index += 1
    cleaned = "".join(cleaned)
    tokens = [(m.group(), text.count("\n", 0, start) + cleaned.count("\n", 0, m.start()) + 1)
              for m in re.finditer(r"'(?:\\.|[^'])*'|%\w+|[A-Za-z_]\w*|\d+|[:|;]", cleaned)]
    result, lhs, rhs, attached, line = [], None, [], [], 0

    def finish():
        if lhs is not None:
            result.append({"lhs": lhs, "rhs": list(rhs), "line": line, "actions": list(attached)})

    i = 0
    while i < len(tokens):
        token, token_line = tokens[i]
        if i + 1 < len(tokens) and tokens[i + 1][0] == ":":
            finish()
            lhs, rhs, attached, line = token, [], [], token_line
            i += 2
            continue
        if token in ("|", ";"):
            finish()
            rhs, attached, line = [], [], token_line
            if token == ";":
                lhs = None
        elif token.startswith("%"):
            if token != "%dprec":
                raise ValueError("unsupported Bison directive: " + token)
            i += 1  # %dprec's numeric argument (no other directive occurs here)
        elif token in actions:
            attached.append(actions[token])
        else:
            rhs.append(token)
        i += 1
    finish()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(args.source), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    if commit != SOURCE or dirty:
        parser.error("audit requires the clean exact pinned source commit")
    grammar = args.source / "src/parser/csql_grammar.y"
    rules = productions(grammar.read_text())
    nonterminals = {rule["lhs"] for rule in rules}
    mapping = re.findall(r'\{(\w+), "([A-Z_0-9]+)", [01]\}',
                         (args.source / "src/parser/keyword.c").read_text())
    words = set("SELECT WITH AS FROM WHERE DISTINCT JOIN INNER LEFT RIGHT OUTER CROSS ON AND OR NOT EXISTS IS NULL".split())
    extras = {"query": ("csql_query", set()), "insert": ("insert_or_replace_stmt", {"INSERT", "INTO", "VALUE", "VALUES"}),
              "update": ("update_stmt", {"UPDATE", "SET"}), "delete": ("delete_stmt", {"DELETE"}),
              "merge": ("merge_stmt", {"MERGE", "INTO", "USING", "WHEN", "MATCHED", "THEN", "UPDATE", "SET", "INSERT", "VALUE", "VALUES"})}
    excluded = {"generic_function_id": "identifier-( feature denied, except INSERT target which is not an expression",
                "insert_expression": "INSERT token denied inside expressions; MERGE allows it only after THEN",
                "paren_plus": "(+) token feature denied",
                "reserved_func": "LEFT/RIGHT followed by ( denied; INSERT is allowed only at statement start or after MERGE THEN",
                "table_set_function_call": "SET followed by ( denied",
                "to_param": "INTO denied except at index 1 before the target"}
    families = {}
    for family, (root, additional) in extras.items():
        terminals = {token for token, word in mapping if word in words | additional}
        terminals |= {"IdName", "DelimitedIdName", "BracketDelimitedIdName", "BacktickDelimitedIdName",
                      "UNSIGNED_INTEGER", "CHAR_STRING", "DOT", "COMP_NOT_EQ", "COMP_GE", "COMP_LE", "SEMICOLON",
                      *[repr(c) for c in "(),.+-*/=<>"]}
        productive = set(terminals)
        while True:
            updated = productive | {r["lhs"] for r in rules if r["lhs"] not in excluded and all(s in productive for s in r["rhs"])}
            if updated == productive:
                break
            productive = updated
        reachable = {"stmt_done"}
        while True:
            updated = reachable | {s for r in rules if r["lhs"] in reachable and r["lhs"] not in excluded
                                   and all(t in productive for t in r["rhs"]) for s in r["rhs"] if s in nonterminals}
            if updated == reachable:
                break
            reachable = updated
        reductions = [r for r in rules if r["lhs"] in reachable and r["lhs"] not in excluded and all(s in productive for s in r["rhs"])]
        families[family] = {"root": "stmt_done", "familyEntry": root, "terminals": sorted(terminals), "nonterminals": sorted(reachable), "reductions": reductions}
    inventory = []
    for rule in rules:
        if any(rule in family["reductions"] for family in families.values()):
            inventory.append(rule)
    counts = {key: len(value["reductions"]) for key, value in families.items()}
    for family in families.values():
        family["reductionIds"] = [inventory.index(rule) for rule in family.pop("reductions")]
    report = {"sourceCommit": SOURCE,
              "grammarSha256": hashlib.sha256(grammar.read_bytes()).hexdigest(),
              "toolSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "coverageRevision": "bounded-query-dml-create-serial-v2", "excludedNonterminals": excluded,
              "limits": "Complete reductions overapproximate adjacency/context checks; not evidence for arbitrary recovery/prefix actions. See manual audit.",
              "families": families, "reductions": inventory}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print({"familyReductions": counts, "unionReductions": len(inventory)})


if __name__ == "__main__":
    main()

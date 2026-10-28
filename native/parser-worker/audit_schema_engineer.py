"""Inventory complete reduction candidates, separate from manual context proof.

The alphabet closure intentionally includes candidates denied by positional
predicates. It cannot prove malformed-prefix, lexer, helper or error paths safe.
SCHEMA_ENGINEER_AUDIT.md supplies that review and records excluded contexts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from audit_query_dml import SOURCE, productions

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(args.source), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    if commit != SOURCE or dirty:
        parser.error("requires clean exact pinned source")
    grammar = args.source / "src/parser/csql_grammar.y"
    rules = productions(grammar.read_text())
    nonterminals = {r["lhs"] for r in rules}
    mapping = re.findall(r'\{(\w+), "([A-Z_0-9]+)", [01]\}', (args.source / "src/parser/keyword.c").read_text())
    query = "SELECT WITH AS FROM WHERE DISTINCT JOIN INNER LEFT RIGHT OUTER CROSS ON AND OR NOT EXISTS IS NULL"
    configs = {
        "create-table": ("CREATE TABLE INT INTEGER SMALLINT BIGINT", "(),", False, False),
        "alter-table": ("ALTER TABLE ADD COLUMN INT INTEGER SMALLINT BIGINT", "(),", False, False),
        "create-view": ("CREATE VIEW AS " + query, "(),.+-*/=<>", True, True),
        "alter-view": ("ALTER VIEW CHANGE QUERY " + query, "(),.+-*/=<>", True, True),
        "drop-entity": ("DROP TABLE VIEW", ",", False, False),
        "create-index": ("CREATE INDEX ON ASC DESC", "(),", False, False),
        "alter-index": ("ALTER INDEX ON REBUILD", "", False, False),
        "drop-index": ("DROP INDEX ON", "", False, False),
        "alter-serial": ("ALTER SERIAL START WITH INCREMENT BY MINVALUE MAXVALUE NOMINVALUE NOMAXVALUE CYCLE NOCYCLE CACHE NOCACHE COMMENT", "+-", True, True),
        "drop-serial": ("DROP SERIAL", "", False, False),
        "describe": ("DESCRIBE DESC EXPLAIN", "", False, True),
        "show-columns": ("SHOW COLUMNS FROM", "", False, False),
        "show-trace": ("SHOW TRACE", "", False, False),
        "evaluate": ("EVALUATE " + query, "(),.+-*/=<>", True, True),
        "statistics": ("UPDATE STATISTICS ON", ",", False, False),
        "set-system": ("SET SYSTEM PARAMETERS", ",", False, True),
        "set-trace": ("SET TRACE ON OFF OUTPUT TEXT JSON", "", False, False),
        "commit": ("COMMIT WORK RETAIN LOCK", "", False, False),
        "rollback": ("ROLLBACK WORK TO SAVEPOINT", "", False, True),
        "savepoint": ("SAVEPOINT", "", False, True),
    }
    names = {"IdName", "DelimitedIdName", "BracketDelimitedIdName", "BacktickDelimitedIdName"}
    families, inventory = {}, []
    for family, (words, punctuation, numbers, strings) in configs.items():
        terminals = {token for token, word in mapping if word in words.split()} | {"SEMICOLON"}
        # The raw overapproximation keeps names even in fixed-word families;
        # the production predicates remove those candidates contextually.
        terminals |= names | {repr(c) for c in punctuation}
        if "." in punctuation: terminals |= {"DOT", "COMP_NOT_EQ", "COMP_GE", "COMP_LE"}
        if numbers: terminals.add("UNSIGNED_INTEGER")
        if strings: terminals.add("CHAR_STRING")
        productive = set(terminals)
        while True:
            updated = productive | {r["lhs"] for r in rules if all(s in productive for s in r["rhs"])}
            if updated == productive: break
            productive = updated
        reachable = {"stmt_done"}
        while True:
            updated = reachable | {s for r in rules if r["lhs"] in reachable and all(t in productive for t in r["rhs"])
                                   for s in r["rhs"] if s in nonterminals}
            if updated == reachable: break
            reachable = updated
        candidates = [r for r in rules if r["lhs"] in reachable and all(t in productive for t in r["rhs"])]
        for rule in candidates:
            if rule not in inventory: inventory.append(rule)
        families[family] = {"root": "stmt_done", "terminals": sorted(terminals), "nonterminals": sorted(reachable),
                            "reductionIds": [inventory.index(r) for r in candidates],
                            "admission": "rejected: disconnected value-clone helper" if family in ("describe", "show-columns") else "bounded predicate, manual context proof required"}
    helpers = ["src/parser/parse_tree.c", "src/parser/parse_tree_cl.c", "src/parser/parser_support.c",
               "src/parser/parse_dbi.c", "src/compat/db_macro.c", "src/compat/db.h", "src/object/schema_manager.c", "src/object/object_primitive.c",
               "src/parser/csql_lexer.l", "src/parser/keyword.c", "src/base/language_support.c",
               "src/base/system_parameter.c", "src/base/error_manager.c", "src/parser/name_resolution.c"]
    bound = {str(Path("source") / p): hashlib.sha256((args.source / p).read_bytes()).hexdigest() for p in helpers}
    for p in [Path(__file__), HERE / "audit_query_dml.py", *sorted((HERE / "coverage").glob("*.hpp"))]:
        bound[str(p.relative_to(HERE))] = hashlib.sha256(p.read_bytes()).hexdigest()
    report = {"sourceCommit": SOURCE, "grammarSha256": hashlib.sha256(grammar.read_bytes()).hexdigest(),
              "boundInputs": bound, "families": families, "candidateReductions": inventory,
              "limits": "Complete alphabet-productive candidates, not an admission or safety proof. Context exclusions, prefix/midrule/error actions and transitive helper branches require the manual audit."}
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(inventory)} distinct candidate reductions across {len(families)} alphabets")


if __name__ == "__main__":
    main()

"""Build a host-qualified executable; all CUBRID inputs are mandatory and explicit."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import shlex
import subprocess

from coverage_keywords import keyword_header

SOURCE = "cc947788d3b7dc402f46192d0f3299ddcc8563ba"
VERSION = "11.5.0.2704-cc94778"
LIBRARY_SHA = "56eb36e9a46e3b6f5258974b25085b81d1679430618041343e4d979704822b33"
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "generated", "library", "runtime-prefix"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--output", type=Path, default=HERE / "build")
    parser.add_argument("--test-internal-error", action="store_true",
                        help="build a nonproduction classifier fault fixture into a separate --output directory")
    args = parser.parse_args()
    if args.test_internal_error and args.output.resolve() == (HERE / "build").resolve():
        parser.error("test-only fault builds require a separate --output directory")
    source, generated, library, prefix = [p.resolve(strict=True) for p in
                                         (args.source, args.generated, args.library, args.runtime_prefix)]
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        parser.error("qualification is limited to Linux x86_64")
    if run("git", "-C", str(source), "rev-parse", "HEAD") != SOURCE:
        parser.error("source commit differs from the qualified profile")
    if run("git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"):
        parser.error("qualified source has tracked modifications")
    if (HERE / "coverage/keywords.hpp").read_text() != keyword_header(source):
        parser.error("coverage keyword inventory differs from the pinned lexer/table")
    if sha(library) != LIBRARY_SHA:
        parser.error("library SHA-256 differs from the qualified profile")
    if f'#define VERSION_STRING "{VERSION}"' not in (generated / "version.h").read_text():
        parser.error("generated version header differs from the qualified profile")
    settings = {"charset": "en_US.utf8", "strings_have_no_escapes": False,
                "ansi_quotes": True, "no_backslash_escapes": False, "pipes_as_concat": True,
                "oracle_style_empty_string": False, "query_trace": False,
                "compat_mode": 0, "intl_check_input_string": True, "intl_collation": "utf8_bin",
                "unicode_input_normalization": False, "unicode_output_normalization": False,
                "parser_use_client_charset": True}
    files = [library]
    files += sorted((prefix / "msg").glob("en_US*/*.cat"))
    files += [prefix / "lib/libcubrid_timezones.so.11.5"]
    if len(files) < 8:
        parser.error("mandatory English runtime message catalogs are missing")
    build_headers = [generated / "config.h", generated / "version.h",
                     generated / "3rdparty/Source/rapidjson/include/rapidjson/document.h",
                     generated / "3rdparty/Source/re2/re2/re2.h"]
    # Record every transitive dynamic dependency resolved by this pinned library.
    worker_libraries = [Path(run("c++", "-print-file-name=" + name)).resolve(strict=True)
                        for name in ("libstdc++.so", "libcrypto.so")]
    dependency_text = "\n".join(run("ldd", str(path)) for path in [library, *worker_libraries])
    if "not found" in dependency_text:
        parser.error("runtime dependency unavailable")
    files += [Path(p) for p in re.findall(r"(?:=>\s+|^\s*)(/\S+)", dependency_text, re.M)]
    files += worker_libraries
    headers = sorted([*source.joinpath("src").rglob("*.h"), *source.joinpath("src").rglob("*.hpp"),
                      *source.joinpath("include").rglob("*.h")])
    header_records = {str(p.relative_to(source)): sha(p) for p in headers}
    worker_inputs = [HERE / "worker.cpp", HERE / "build.py", HERE / "coverage_keywords.py", *sorted((HERE / "coverage").glob("*.hpp"))]
    manifest = {"profile": "cubrid-" + VERSION, "testOnly": args.test_internal_error,
                "workerInputs": {str(p.relative_to(HERE)): sha(p) for p in worker_inputs},
                "limits": {"addressSpaceBytes": 512 * 1024 * 1024, "documentBytes": 8 * 1024 * 1024,
                           "frameBytes": 64 * 1024 * 1024, "diagnostics": 256}, "sourceCommit": SOURCE,
                "nativeVersion": VERSION, "platform": "linux-x86_64", "settings": settings,
                "host": {"platform": platform.platform(), "libc": platform.libc_ver()},
                "coverageRevision": "bounded-query-dml-create-serial-v2",
                "supportedStatementKinds": ["PT_SELECT", "PT_INSERT", "PT_UPDATE", "PT_DELETE", "PT_MERGE", "PT_CREATE_SERIAL"],
                "grammarInputs": {str(p): sha(p) for p in (source / "src/parser" / name for name in
                    ("csql_grammar.y", "csql_lexer.l", "keyword.c", "parse_tree.c", "parse_tree_cl.c", "parser_support.c", "name_resolution.c"))},
                "source": str(source), "library": str(library), "runtimePrefix": str(prefix),
                "files": {str(p.resolve(strict=True)): sha(p) for p in files},
                "generatedHeaders": {str(p): sha(p) for p in build_headers},
                "headers": header_records,
                "headerSetSha256": hashlib.sha256(json.dumps(header_records, sort_keys=True).encode()).hexdigest()}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (output / "manifest.json").write_text(manifest_text)
    digest = hashlib.sha256(manifest_text.encode()).hexdigest()
    (output / "qualification.hpp").write_text(
        '#pragma once\nstatic constexpr const char *manifest_sha = ' + json.dumps(digest) + ';\n')
    includes = sorted({p.parent for p in headers} | {source / "include"})
    rapidjson = generated / "3rdparty/Source/rapidjson/include"
    if not (rapidjson / "rapidjson/document.h").is_file():
        parser.error("mandatory RapidJSON 1.1 headers are missing from explicit generated input")
    command = ["c++", "-std=c++17", "-O2", "-DCS_MODE", "-fno-strict-aliasing", "-Wno-deprecated-declarations",
               "-MMD", "-MF", str(output / "headers.d"),
               "-I" + str(output), "-I" + str(generated), "-I" + str(rapidjson),
               "-I" + str(generated / "3rdparty/include"),
               "-I" + str(generated / "3rdparty/Source/re2"),
               *["-I" + str(p) for p in includes], str(HERE / "worker.cpp"), "-o", str(output / "parser-worker"),
               "-ldl", "-lcrypto"]
    if args.test_internal_error:
        command.insert(1, "-DCUBRID_PARSER_TEST_INTERNAL_ERROR")
    subprocess.run(command, check=True)
    dependencies = shlex.split((output / "headers.d").read_text().replace("\\\n", " ").partition(":")[2])
    (output / "build-evidence.json").write_text(json.dumps({"compiler": run("c++", "--version"),
        "command": command, "manifestSha256": digest, "workerSha256": sha(output / "parser-worker"),
        "compiledInputs": {str(Path(path).resolve()): sha(Path(path)) for path in dependencies},
        "dynamicDependencies": run("ldd", str(output / "parser-worker"))}, indent=2) + "\n")
    print(output / "parser-worker")


if __name__ == "__main__":
    main()

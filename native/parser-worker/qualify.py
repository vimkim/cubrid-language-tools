"""Retain fixed parse-only fixtures and syscall containment evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build, output = args.build.resolve(strict=True), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    corpus = json.loads((HERE / "qualification/corpus.json").read_text())
    fixtures = corpus["cases"]
    requests = [{"protocolVersion": 1, "id": 1, "method": "initialize", "profile": "cubrid-11.5.0.2704-cc94778"}]
    requests += [{"protocolVersion": 1, "id": i + 2, "method": "parse", "text": case["text"]}
                 for i, case in enumerate(fixtures)]
    requests.append({"protocolVersion": 1, "id": len(requests) + 1, "method": "shutdown"})
    trace_path = output / "syscalls.strace"
    command = ["strace", "-f", "-e", "trace=network,process,openat", "-o", str(trace_path),
               str(build / "parser-worker"), "--manifest", str(build / "manifest.json")]
    process = subprocess.run(command, input="".join(json.dumps(r, ensure_ascii=False) + "\n" for r in requests),
        capture_output=True, text=True, encoding="utf-8", timeout=20,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": "/nonexistent",
             "CUBRID_CONF": "/must-ignore-ambient-config", "CUBRID_DATABASES": "/must-ignore-ambient-registry"})
    if process.returncode:
        raise RuntimeError(f"traced worker failed: {process.stderr}")
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    if (len(responses) != len(requests) or responses[0].get("status") != "ready"
            or responses[0].get("coverageRevision") != corpus["coverageRevision"]
            or responses[-1].get("status") != "closed"):
        raise RuntimeError("incomplete qualification responses")
    cases = [{**case, "response": response} for case, response in zip(fixtures, responses[1:])]
    if any(case["response"]["status"] != case["expected"]
           or case["response"]["statementKinds"] != case["kinds"]
           or [d["admitted"] for d in case["response"]["coverageDecisions"]] != case["admitted"]
           or len(case["response"]["nativeObservations"]) != sum(case["admitted"])
           or not case["response"].get("syntaxSettingsUnchanged")
           or any(o["nativeErrorId"] != 0 for o in case["response"]["nativeObservations"]) for case in cases):
        raise RuntimeError("qualification fixture failed")
    trace = trace_path.read_text()
    network = [line for line in trace.splitlines() if re.search(r"\b(socket|socketpair|connect|bind|listen|accept|sendto|recvfrom|sendmsg|recvmsg)\(", line)]
    executions = [line for line in trace.splitlines() if "execve(" in line]
    descendants = [line for line in trace.splitlines() if re.search(r"\b(clone|clone3|fork|vfork)\(", line)]
    writable = [line for line in trace.splitlines() if "openat(" in line and re.search(r"O_WRONLY|O_RDWR|O_CREAT|O_TRUNC", line)]
    outside = [line for line in writable if '"/tmp/cubrid-parser-worker-' not in line]
    if network or len(executions) != 1 or descendants or outside:
        raise RuntimeError("parse-only containment trace failed")
    for filename in ("manifest.json", "build-evidence.json"):
        shutil.copyfile(build / filename, output / filename)
    report = {"command": command, "initialize": responses[0], "cases": cases,
              "evidenceSha256": {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (HERE / "qualification/corpus.json", HERE / "qualification/query-dml-reductions.json",
                                              HERE / "qualification/schema-engineer-reductions.json", HERE / "qualification/rejected-candidates.json",
                                              HERE / "audit_query_dml.py", HERE / "audit_schema_engineer.py", HERE / "coverage_keywords.py",
                                              HERE / "AUDIT.md", HERE / "QUERY_DML_AUDIT.md", HERE / "SCHEMA_ENGINEER_AUDIT.md",
                                              HERE / "ORDERED_HINT_AUDIT.md")},
              "trace": {"sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
                        "networkCalls": network, "executions": executions, "descendants": descendants,
                        "writableOpens": writable, "externalWritableOpens": outside},
              "limits": "This trace qualifies the listed corpus only; process separation is not a syscall sandbox.",
              "coordinatePolicy": "Observed columns count UTF-8 bytes (1-based); missing/negative coordinates occur. All diagnostics use original statement spans."}
    (output / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"qualified {len(cases)} fixtures; no network, descendants or external writable opens")


if __name__ == "__main__":
    main()

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
    fixtures = [
        ("serial-valid", "CREATE SERIAL order_no START WITH 10 INCREMENT BY 2;", "valid"),
        ("serial-invalid", "CREATE SERIAL order_no START WITH ;", "syntax-error"),
        ("serial-unicode-invalid", "-- 한글 😀\r\nCREATE SERIAL 주문 START WITH ;", "syntax-error"),
        ("serial-partial-stack", "CREATE SERIAL s START WITH 1 START WITH 2;", "syntax-error"),
        ("serial-options", "CREATE SERIAL s START WITH -10 INCREMENT BY +2 MINVALUE -20 MAXVALUE 100 CYCLE CACHE 8 COMMENT '가😀';", "valid"),
        ("serial-disabled-options", "CREATE SERIAL s NOMINVALUE NOMAXVALUE NOCYCLE NOCACHE;", "valid"),
        ("serial-cache-overflow", "CREATE SERIAL s CACHE 2147483648;", "syntax-error"),
        ("serial-comment-concatenation", "CREATE SERIAL s COMMENT 'a' 'b';", "valid"),
        ("literal-valid", "SELECT '한글 😀', -10, NULL;", "valid"),
        ("literal-boundaries", "SELECT 99999999999999999999999999999999999999, +2, -9223372036854775808, NULL, 'a''b', 'a\\n';", "valid"),
        ("semicolon-optional", "SELECT 1", "valid"),
        ("unterminated-string", "SELECT '가😀", "syntax-error"),
        ("unterminated-comment", "SELECT 1 /* unfinished", "syntax-error"),
        ("syntax-and-unsupported", "SELECT 1,; DROP TABLE never_execute;", "syntax-error"),
        ("literal-invalid", "SELECT 1 2;", "syntax-error"),
        ("incomplete", "SELECT 1,", "syntax-error"),
        ("empty", "", "valid"),
        ("multiple", "SELECT 1; CREATE SERIAL order_no START WITH 10;", "valid"),
        ("korean-coordinate", "SELECT '가', ;", "syntax-error"),
        ("emoji-coordinate", "SELECT '😀', ;", "syntax-error"),
        ("crlf-coordinate", "SELECT '가😀'\r\n, ;", "syntax-error"),
        ("catalog-query-blocked", "SELECT * FROM missing_table;", "unsupported"),
        ("cte-blocked", "WITH x AS (SELECT 1) SELECT 1;", "unsupported"),
        ("subquery-blocked", "SELECT (SELECT 1);", "unsupported"),
        ("destructive-text-blocked", "DROP TABLE must_never_be_executed;", "unsupported"),
    ]
    requests = [{"protocolVersion": 1, "id": 1, "method": "initialize", "profile": "cubrid-11.5.0.2704-cc94778"}]
    requests += [{"protocolVersion": 1, "id": i + 2, "method": "parse", "text": text}
                 for i, (_, text, _) in enumerate(fixtures)]
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
    if len(responses) != len(requests) or responses[0].get("status") != "ready":
        raise RuntimeError("incomplete qualification responses")
    cases = [{"id": name, "text": text, "expected": expected, "response": response}
             for (name, text, expected), response in zip(fixtures, responses[1:])]
    if any(case["response"]["status"] != case["expected"] for case in cases):
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
              "trace": {"sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
                        "networkCalls": network, "executions": executions, "descendants": descendants,
                        "writableOpens": writable, "externalWritableOpens": outside},
              "limits": "This trace qualifies the listed corpus only; process separation is not a syscall sandbox.",
              "coordinatePolicy": "Observed columns count UTF-8 bytes (1-based); missing/negative coordinates occur. All diagnostics use original statement spans."}
    (output / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"qualified {len(cases)} fixtures; no network, descendants or external writable opens")


if __name__ == "__main__":
    main()

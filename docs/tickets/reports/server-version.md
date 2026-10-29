# Installed server version report

## Design and baseline

The dispatch baseline is `f8b98c79682197b9b5d3587adc9e4897131e08ed` on `main`.
The launcher captures the whole argument list as a tuple. It accepts no arguments, standalone `--version`, and standalone `--help` or `-h`. Other invocations exit 3 and write guidance to stderr. The no-argument path retains the existing stdio startup.

The version query reads `cubrid-language-tools` distribution metadata with the Python standard library before importing optional server dependencies. Missing metadata produces installation guidance and exit 3. Help does not require metadata. Neither information query needs the native runtime.

Two independent design candidates chose exact argument matching. The coordinator
read both candidates and selected the first candidate's whole-invocation tuple
matching and isolated metadata test design. Both candidates reached the same
shape, so no graft was needed. A different-family cross-judge was unavailable
because all configured and available models belong to the GPT family.

| Alternative | Decision |
| --- | --- |
| Match complete argument tuples in the existing launcher | Selected. Preserves standalone options and exit 3 without another interface. |
| Introduce an argument parser | Rejected. Custom error exits and exclusivity checks add policy for three standalone spellings. |

## Acceptance evidence

- `python3 -m unittest discover -s tests -p test_lsp_bootstrap.py -v` failed against the baseline after the tests were added. The baseline rejected the version and help flags and did not provide the required error guidance. The log is `/home/vimkim/temp/cubrid-server-version.mCmbJQ/implementation/red.log`.
- The same command passed all 6 tests after implementation. The tests use `python -S`, a copied source package, and isolated temporary metadata with version `9.8.7`. The log is `/home/vimkim/temp/cubrid-server-version.mCmbJQ/implementation/green.log`.
- `just test` passed 124 tests. The log is `/home/vimkim/temp/cubrid-server-version.mCmbJQ/implementation/core.log`.
- `git diff --check` passed after the implementation and guide changes.
- Built a wheel with `uv build --wheel` and installed it outside the checkout in isolated core-only Python 3.10 and LSP-enabled Python 3.14 environments. Both installed console scripts and `python -I -m cubrid_language.lsp --version` printed `cubrid-language-server 0.1.0.dev0`, exited 0, and left stderr empty.
- Both installed environments passed `--help`, `-h`, unknown options, mixed options in both orders, extra arguments, abbreviated options, and repeated version options. Invalid invocations exited 3 with empty stdout.
- The core-only installed distribution inventory contained only `cubrid-language-tools`. No-argument startup retained missing-extra guidance and exit 3 with empty stdout. Its installed-package core suite passed 124 tests on Python 3.10.
- The LSP-enabled installed package passed all 34 existing protocol tests on Python 3.14. It exercised framed initialization, completion, shutdown, and protocol-only stdout.
- The scoped comment review found no added or changed comments or docstrings, no findings, and no remaining review constraints. The coordinator reviewed the complete implementation and documentation diff before committing.

The installed checks can be repeated with:

```sh
python3 /home/vimkim/temp/cubrid-server-version.mCmbJQ/verify_installed.py \
  --root /home/vimkim/gh/cubrid-language-tools-server-version \
  --evidence /absolute/fresh/evidence-directory
```

The verification script, command records, stdout, stderr, wheel, and isolated
environments are preserved under
`/home/vimkim/temp/cubrid-server-version.mCmbJQ`.

## Principles applied

- Model the Domain led to matching the complete launch argument tuple.
- Laziness Protocol kept the command in the existing bootstrap and avoided a separate version module or executable.
- Test Behavior, Not Implementation led to public subprocess assertions and the distinctive metadata version `9.8.7`.
- Prove It Works led to installed-wheel checks outside the checkout and real framed LSP tests.
- Exhaust the Design Space led to comparison of exact dispatch and an argument parser before implementation.
- Separate Before Serializing Shared State gave design candidates separate output directories and implementation one worktree owner.
- Sequence Work into Verifiable Units ordered failing tests, implementation, passing tests, installed verification, and commit.

## Throughput checkpoint

- Blocking first steps. Read the baseline, contracts, ticket, and agreed design before the public-interface tests.
- Independent workstreams. The coordinator owns installed-wheel and LSP protocol verification. Implementation and paired guides belong to this ticket owner.
- Shared mutable state. Only the ticket owner edits implementation files. Packaging and shared recipes stay unchanged.
- Smallest safe decomposition. One implementation owner keeps argument dispatch, tests, and paired documentation consistent.

## Remaining limitations

Source-only execution without installed distribution metadata cannot report a
version. The command reports the package version, not a Git commit or CUBRID
parser profile. Development builds that share `0.1.0.dev0` remain indistinguishable
by package version alone. LSP `serverInfo` is unchanged and can diverge from
installed distribution metadata in a future release.

The user's PATH installation is unchanged. Local integration into `main` and its
required push await explicit approval. User-level reinstallation and native-parser
qualification were not part of this ticket.

# Install and qualify the development release

[한국어](install.md) | **English** · [Documentation](README.en.md)

Use Python 3.10 or later. This local development release is `0.1.0.dev0`.
The commands below install a local checkout or built artifact. They do not assume publication to a package index.
See [qualified coverage](coverage.en.md) before interpreting a syntax pass.
If your existing installation uses native diagnostics, follow the [paired upgrade steps](#upgrade-the-core-and-worker-together) before reinstalling the package.

## Install commands on PATH

With uv and just available, run from the checkout:

```sh
just sync
cubrid-lint --help
cubrid-language-server --version
```

`just install` is an alias for `just sync`.
Both run `uv tool install --reinstall '.[lsp]'` to install the CLI, LSP, and pinned optional dependencies in a uv tool environment.
Run either command again to reinstall the current checkout.
If your shell cannot find the commands, run `uv tool update-shell` and restart the shell.
Configure your editor to spawn `cubrid-language-server` from PATH with no arguments and stdio transport.
Completion works immediately. Strict diagnostics also require the separate native worker and runtime described below.

## Install the core and CLI

Clone the public repository and create a dedicated environment:

```sh
git clone https://github.com/vimkim/cubrid-language-tools.git
cd cubrid-language-tools
```

Install the package:

```sh
uv venv --python 3.10 .venv
uv pip install --python .venv/bin/python .
.venv/bin/cubrid-lint --help
.venv/bin/python -I -c "from cubrid_language import complete; print(complete('sel', 3, 'cubrid-11.5.0.2704-cc94778'))"
```

Core and CLI have zero mandatory Python runtime dependencies.
Completion works immediately. Strict linting also needs the trusted native inputs described below.
The package installs both console commands. `cubrid-language-server --version` prints the installed distribution version without the optional extra or native runtime.
The current value `0.1.0.dev0` identifies neither a Git commit nor the native coverage revision.
Without the optional extra, starting the server with no arguments prints guidance to stderr and exits 3.
A source-only invocation without installed distribution metadata cannot report a version. Install the package first.

To install an artifact instead, build it and choose one of these inputs:

```sh
uv build
uv pip install --python .venv/bin/python dist/cubrid_language_tools-0.1.0.dev0-py3-none-any.whl
```

The source distribution `dist/cubrid_language_tools-0.1.0.dev0.tar.gz` is also installable.
Build isolation requires setuptools 77.0.3 or later. That build dependency is separate from runtime requirements.
The [release qualification recipe](#qualify-a-local-release) tests the exact minimum backend.

## Install the optional stdio server

From the checkout, install the pinned extra in the caller's environment:

```sh
uv pip install --python .venv/bin/python '.[lsp]'
```

For a local wheel, use `'dist/cubrid_language_tools-0.1.0.dev0-py3-none-any.whl[lsp]'`.
The extra pins pygls 2.1.1, lsprotocol 2025.0.0, attrs 25.4.0, cattrs 25.3.0, and typing-extensions 4.15.0.
Python 3.10 also uses exceptiongroup 1.3.1.
Configure an editor to spawn `.venv/bin/cubrid-language-server` with no arguments and stdio transport.
Open documents with language ID `cubrid`. See the [LSP settings guide](lsp.en.md).
See the installation instructions for the [VS Code extension](https://github.com/vimkim/cubrid-vscode) and [Neovim plugin](https://github.com/vimkim/cubrid.nvim).
Neither package bundles or automatically downloads the Python server or native runtime. Keyword completion needs the server but not the native parser.

## Supply the qualified native worker

Strict checks require Linux x86-64 and the exact CUBRID development profile `cubrid-11.5.0.2704-cc94778`.
Supply the pinned source, matching generated headers, library, and runtime assets.
Use a C++17 compiler, OpenSSL development headers, and libcrypto. Trace qualification also requires strace.
Build the worker with the four explicit inputs in the [native instructions](../native/parser-worker/README.md#reproduce-this-host-qualification).
Do not substitute current source headers for the pinned commit or choose a nearby library version.

Keep the production worker, its embedded-digest `manifest.json`, build evidence, and notices together in a trusted directory.
Keep the exact runtime files at their qualified manifest paths.
Moving those inputs requires rebuilding and qualification. Editing a manifest invalidates its digest.
The Python wheel does not contain the worker or runtime. The source archive contains worker source, build scripts, audits, fixtures, and notices.
The tools never download a runtime automatically.

Run an isolated stdin example with explicit trusted paths:

```sh
printf 'SELECT 1;\n' | .venv/bin/cubrid-lint \
  --parser-worker /absolute/trusted/parser-worker \
  --runtime-prefix /absolute/qualified/runtime \
  --format json -
```

The result has status `valid`, coverage `complete`, and exit 0 under the qualified profile.
For `DESCRIBE absent;`, expect `unsupported`, coverage `none`, code `CUBRID-U1002`, and exit 2.
Use [the shared Validator example](lint-cli.en.md#python-interfaces) for direct library validation.
Worker/runtime paths come from explicit CLI flags or trusted user/editor settings.
Project `.cubrid-language.json` can contain only profile, script mode, and snapshot metadata.

Editors and the CLI spawn owned children and use pipes. Language operations require no TCP listener, database connection, SQL execution, or shared daemon.
The native manifest binds source, headers, library/runtime hashes, settings, platform, and the exact coverage revision.
Missing or mismatched inputs produce explicit unsuccessful results, including for empty documents.
Default bounds are a 5-second request deadline, 8 MiB input, 16 MiB reply, and 256 diagnostics.
Abrupt termination can leave the worker's private temporary directory. Normal close removes its own directory.

## Upgrade the core and worker together

Current source requires `bounded-query-dml-schema-engineer-ordered-v4`.
An older v3 installation can have the same CUBRID profile and package version. Its worker still fails the v4 core's identity checks.
Installing the Python package with `just sync` does not rebuild or replace native assets.

1. Select the core checkout you intend to install and record its commit with `git rev-parse HEAD`.
2. Build and qualify a new worker and manifest from that checkout with the four exact native inputs above.
3. Install the core package from the same checkout or its wheel. Keep the new worker, manifest, build evidence, and notices together.
4. Point trusted CLI or editor settings at the new worker and matching runtime. Restart the language server and check a supported example.

Keep the old package and worker together until you switch both. Do not edit a v3 manifest to claim v4.
For the v4 pair, `SELECT /*+ ORDERED */ 1;` returns `valid`, while `SELECT /*+ ORDERED */ 1 FROM absent;` remains `unsupported`.
See [qualified coverage](coverage.en.md) for the complete boundary.

## Qualification evidence

The [original distribution report](tickets/reports/09.md) records the full eight-environment v3 matrix.
That matrix has not been rerun for v4. Its historical v3 results do not qualify a v4 distribution release.
The v4 implementation at core commit `057e41b` passed the core, native, framed LSP, and native LSP suites.
It also has a source-matched installed wheel check and real OpenVSCode 1.109.5 acceptance with the matching v4 worker.
The [ORDERED report](tickets/reports/native-ordered.md) records the native boundary and corpus.
The [ticket index](tickets/README.md) distinguishes integrated work from each report's original review state.
These checks do not establish new v4 acceptance in Microsoft desktop VS Code or Neovim, or a complete v4 distribution matrix.

## Qualify a local release

Install uv and make Python 3.10 and 3.14 available. Build the matching v4 worker from the exact native inputs first.
Use a new output directory to preserve commands, logs, environments, and artifacts:

```sh
just test
just test-native-parser
just test-lsp
just test-lsp-native
just qualify-release native/parser-worker/build /absolute/new/release-evidence
```

The release recipe forces setuptools 77.0.3 for isolated wheel and source builds on both Python versions.
It installs core and optional artifacts in eight separate environments outside the checkout.
Archive checks compare source and notice bytes, both console entry points, six optional-only requirements, and absence of compiled native outputs.
Portable fixtures compare installed library and CLI status, coverage, codes, and original spans.
Optional installs also compare ordered completion edits and framed UTF-16 diagnostics with literal Unicode/CRLF expectations.
LSP transports diagnostic consequences of status and coverage. It does not add status or coverage protocol fields.
Core installs run the default suite and missing-extra command. Optional installs run the framed suite and check dependency versions.
Native/optional prerequisites must fail visibly when absent. They never become skipped qualification.
This recipe preserves source, runtime, database, daemon, and remote state.

## Preserve license and notice files

Project code uses [Apache License 2.0](../LICENSE).
SPDX metadata uses `license = "Apache-2.0"` with explicit license files.
The migration follows the [setuptools guide](https://setuptools.pypa.io/en/stable/userguide/license_migration.html)
and the [Python packaging guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).
Both archives retain the project license and the 17 native component texts with their inventory.
The wheel stores these under its distribution metadata's `licenses` directory.

The [native notice inventory](../native/parser-worker/notices/README.md) records separately supplied CUBRID, header, and system dependencies.
Metadata does not establish legal clearance for a redistributed runtime bundle.
Preserve original attribution and actual component terms with any native delivery.

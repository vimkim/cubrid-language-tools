# Completion provenance

The independent completion library preserves the tolerant algorithm from csql-future checkpoint
`ea796ad6611fa0090003f9698e6d635b8978591a`.
It does not import csql-future or acquire catalog metadata.
Callers provide the original text, cursor, profile identifier, and optional immutable schema values.

## Vocabulary and profile identity

| Material | Recorded origin | Scope |
| --- | --- | --- |
| Parameter names, types, dynamic flags, DBA flags, and SHOW fields | CUBRID 11.4 manual, `CUBRID/cubrid-manual@e5f10c4542d24a50b83334a68ccc4a91278b9cf0` | 137 parameters and seven SHOW field sets |
| Inspection, management, and session completion rules | Checkpoint `syntax.py`, documented there as CUBRID 11.4 completion grammar | 47 session command names, including the consumer command `;refresh-completions` |
| Identifier quoting | Checkpoint reserved-word snapshot, documented there as CUBRID 11.5 `src/parser/keyword.c` and manual | Quoting decisions, separate from the smaller suggested keyword list |
| Generic keywords, token spans, aliases, and ordering | Preserved completion checkpoint | Tolerant suggestions for incomplete text |

[completion_data.py](../src/cubrid_language/completion_data.py) is byte-identical to the checkpoint.
Its header retains the original generator name and exact manual revision.
That generator belongs to the preserved csql-future project.
[syntax.py](../src/cubrid_language/syntax.py) retains all rules and values.
Its introductory description now states that completion rules do not validate syntax.

The strict parser's first target is `cubrid-11.5.0.2704-cc94778`, bound to CUBRID source
`cc947788d3b7dc402f46192d0f3299ddcc8563ba`.
Completion does not qualify that profile or claim that its 11.4 vocabulary matches every 11.5 feature.
The current `profile` argument records explicit caller context without selecting a different vocabulary.
An unavailable parser does not disable completion.
Strict validation and its supported coverage remain separate delivery gates.

## Port and parity

The port moves immutable completion and schema values into `cubrid_language.models`.
It preserves the repository's existing `Span` implementation.
Collection fields take tuple snapshots so later changes to caller lists cannot change stored values.
The public package exports `complete`, `Span`, `CompletionItem`, `CompletionResult`, `Relation`, and `Schema`.

At the ticket 01 port, thirteen algorithm functions retained identical syntax trees after renaming the item and internal suggestion values.
The two wrapper changes remove the legacy availability-message argument and construct the shared central result.
The package contains no terminal menu, compatibility entry point, catalog loader, or CSQL execution path.
Session command suggestions describe names and arguments only.

[The parity fixture](../tests/fixtures/completion-ea796ad.json) contains 230 distinct public suggestion observations
from the checkpoint's 20 context and command tests, across six schema values.
Each observation records the original text, cursor, ordered item values, replacement range, and allowed flag.
Central tests compare the complete public result with these recorded values.
They also call the full corpus twice while blocking filesystem, environment, network, subprocess, and terminal boundaries.

To reproduce the fixture from the preserved checkpoint, run this optional development command:

```bash
python3 -B tests/fixtures/capture_completion_fixture.py \
  /home/vimkim/gh/csql-future-language-01 \
  --output /tmp/completion-ea796ad.json
cmp tests/fixtures/completion-ea796ad.json /tmp/completion-ea796ad.json
```

The generator requires the exact, clean checkpoint and disables bytecode writes before importing it.
The installed package and ordinary test suite do not need that checkout.
The source archive includes the JSON fixture so its tests can run independently.

## Retained limits

The algorithm remains a completion heuristic, not a parser, semantic analyzer, or full SQL grammar.
Unknown schema metadata produces no invented relation or column names.
Ordinary strings and comments suppress completion.
The existing `SET SYSTEM PARAMETERS` string context provides parameter completion as an explicit exception.
Consumers own metadata refresh and availability messages.
The immutable result reserves its optional `availability` field for future use and currently returns `None`.

The repository retains its Apache-2.0 license.
This port changes no existing source notices.
Native runtime notices and final release qualification belong to later tickets.

## Intentional delivery corrections

Ticket 09 keeps the original 230 observations and their capture file unchanged.
Final public-interface review identified missing CUBRID `//` comments and backslash escapes in single-quoted strings.
The tokenizer now protects those lexical regions under the qualified profile settings.
Session completion now selects the current command line and preserves full-document offsets.
Earlier command arguments no longer enter later SQL context, while quoted lexical blocks still span lines.
Bare SQL terminators and terminators followed by ordinary comments preserve their statement boundary.
Public library and framed LSP regressions record these intentional corrections separately from the historical parity corpus.
The public completion value also handles empty or incomplete display details without changing existing kinds or constructor arguments.

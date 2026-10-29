default:
    @just --list

sync:
    uv tool install --reinstall '.[lsp]'

alias install := sync

test:
    uv run python -m unittest discover -s tests -v

test-language-core:
    uv run python -m unittest discover -s tests -p 'test_completion*.py' -v

build:
    uv build

build-native-parser source generated library runtime_prefix:
    python3 native/parser-worker/build.py --source '{{source}}' --generated '{{generated}}' --library '{{library}}' --runtime-prefix '{{runtime_prefix}}'

test-native-parser:
    PYTHONPATH=src python3 -m unittest discover -s tests/native_parser -v
    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validation_*.py' -v

test-lsp:
    uv run --extra lsp python -m unittest discover -s tests/lsp -v

test-lsp-native:
    uv run --extra lsp python -m unittest discover -s tests/lsp_native -v

qualify-release build output:
    python3 tools/qualify_release.py --build '{{build}}' --output '{{output}}'

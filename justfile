default:
    @just --list

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

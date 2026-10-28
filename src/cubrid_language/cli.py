"""Offline lint input and output adapter. SQL decisions belong to the library."""

import argparse
import json
from pathlib import Path
import sys

from .config import ConfigError, resolve_config
from .validation import PROFILE, Diagnostic, DocumentMap, Span, ValidationResult, Validator, WorkerConfig

_EXIT = {'valid': 0, 'unsupported': 2, 'syntax-error': 1, 'tool-error': 3}
_PRIORITY = {'valid': 0, 'unsupported': 1, 'syntax-error': 2, 'tool-error': 3}
_DOCUMENT_LIMIT = 8 * 1024 * 1024


class _ArgumentsError(ValueError):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgumentsError(message)


def _parser():
    parser = _Parser(prog='cubrid-lint', allow_abbrev=False, description='Check CUBRID text offline without executing SQL.')
    parser.add_argument('--profile')
    parser.add_argument('--script-mode', choices=('sql', 'csql'))
    parser.add_argument('--format', choices=('human', 'json'), default='human')
    parser.add_argument('--config', metavar='PATH')
    parser.add_argument('--parser-worker', metavar='PATH')
    parser.add_argument('--runtime-prefix', metavar='PATH')
    parser.add_argument('paths', nargs='+', metavar='PATH')
    return parser


def _input_failure(profile, message):
    return ValidationResult('tool-error', 'none', profile, (
        Diagnostic('CUBRID-T1003', 'error', message, Span(0, 0), 'exact', 'tool'),))


def _read(path):
    if path == '-':
        data = sys.stdin.buffer.read(_DOCUMENT_LIMIT + 1)
    else:
        with Path(path).open('rb') as stream:
            data = stream.read(_DOCUMENT_LIMIT + 1)
    if len(data) > _DOCUMENT_LIMIT:
        raise ValueError('input exceeds the 8 MiB document byte limit')
    return data.decode('utf-8', errors='strict')


def _write_human(documents, texts):
    for document, text in zip(documents, texts):
        positions = DocumentMap(text)
        for diagnostic in document['diagnostics']:
            line, column = positions.human_location(diagnostic['span']['start'])
            message = diagnostic['message'].replace('\r', '\\r').replace('\n', '\\n')
            print(f"{document['path']}:{line}:{column}: {diagnostic['severity']} {diagnostic['code']} {message}")
        print(f"{document['path']}: {document['status']} ({document['coverage']}, {document['profile']})")


def main(argv=None):
    parser = _parser()
    try:
        args = parser.parse_intermixed_args(argv)
    except _ArgumentsError as error:
        parser.print_usage(sys.stderr)
        print(f'cubrid-lint: error: {error}', file=sys.stderr)
        return 3

    configuration_error = None
    worker_config = None
    try:
        if bool(args.parser_worker) != bool(args.runtime_prefix):
            raise ValueError('--parser-worker and --runtime-prefix must be supplied together')
        if args.parser_worker is not None:
            worker_config = WorkerConfig(Path(args.parser_worker).absolute(), Path(args.runtime_prefix).absolute())
    except (ValueError, TypeError, OSError) as error:
        configuration_error = str(error)
    if args.paths.count('-') > 1:
        configuration_error = 'stdin (-) may appear only once'

    documents, texts = [], []
    with Validator(worker_config) as validator:
        for path in args.paths:
            text = ''
            profile = args.profile if args.profile is not None else PROFILE
            mode = args.script_mode or ('csql' if Path(path).suffix.lower() == '.csql' else 'sql')
            try:
                settings = resolve_config(None if path == '-' else path, config_path=args.config,
                                          profile=args.profile, script_mode=args.script_mode)
                profile, mode = settings.profile, settings.script_mode
                if configuration_error is not None:
                    raise ValueError(configuration_error)
                text = _read(path)
                result = validator.validate(text, profile, mode)
            except (ConfigError, OSError, UnicodeError, ValueError) as error:
                result = _input_failure(profile, f'cannot check input: {error}')
            documents.append({'path': path, 'scriptMode': mode, **result.to_dict()})
            texts.append(text)
    status = max((document['status'] for document in documents), key=_PRIORITY.__getitem__)
    if args.format == 'json':
        print(json.dumps({'schemaVersion': 1, 'offsetEncoding': 'unicode-codepoints',
                          'documents': documents, 'status': status}, ensure_ascii=True))
    else:
        _write_human(documents, texts)
    return _EXIT[status]


if __name__ == '__main__':
    raise SystemExit(main())

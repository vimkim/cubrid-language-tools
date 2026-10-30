"""One-shot schema export. Only this explicit command connects to CSQL."""

import argparse
import json
import os
import selectors
import signal
import sys
from threading import Event
import time

from .acquisition import (AcquisitionError, MAX_REQUEST_BYTES, acquire_schema,
                          parse_connection, snapshot_json, validate_timeout)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise AcquisitionError('invalid-request')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AcquisitionError('invalid-request')
        result[key] = value
    return result


def _read_request(deadline, cancelled):
    data = bytearray()
    fd = sys.stdin.fileno()
    blocking = os.get_blocking(fd)
    try:
        os.set_blocking(fd, False)
        with selectors.SelectSelector() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while True:
                if cancelled.is_set():
                    raise AcquisitionError('cancelled')
                if time.monotonic() >= deadline:
                    raise AcquisitionError('timeout')
                if not selector.select(min(.02, max(0, deadline - time.monotonic()))):
                    continue
                chunk = os.read(fd, min(65536, MAX_REQUEST_BYTES - len(data) + 1))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > MAX_REQUEST_BYTES:
                    raise AcquisitionError('invalid-request')
    finally:
        os.set_blocking(fd, blocking)
    try:
        request = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs)
    except (ValueError, RecursionError):
        raise AcquisitionError('invalid-request') from None
    if (not isinstance(request, dict) or request.keys() - {'requestVersion', 'command', 'password'}
            or type(request.get('requestVersion')) is not int or request['requestVersion'] != 1
            or not isinstance(request.get('command'), str)):
        raise AcquisitionError('invalid-request')
    return parse_connection(request['command'], password=request.get('password'))


def main(argv=None):
    cancelled = Event()
    handlers = {}
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            handlers[sig] = signal.signal(sig, lambda signum, frame: cancelled.set())
        parser = _Parser(prog='cubrid-schema', description=__doc__, allow_abbrev=False)
        parser.add_argument('action', choices=('export',))
        parser.add_argument('--csql', default='csql', metavar='PATH')
        parser.add_argument('--timeout', default=5, type=float, metavar='SECONDS')
        parser.add_argument('--request-stdin', action='store_true', help='read a version 1 JSON connection request')
        arguments = list(sys.argv[1:] if argv is None else argv)
        connection_args = []
        if '--' in arguments:
            offset = arguments.index('--')
            connection_args = arguments[offset + 1:]
            arguments = arguments[:offset]
        options = parser.parse_args(arguments)
        timeout = validate_timeout(options.timeout)
        deadline = time.monotonic() + timeout
        if options.request_stdin and connection_args:
            raise AcquisitionError('invalid-request')
        if os.name != 'posix':
            raise AcquisitionError('platform')
        connection = (_read_request(deadline, cancelled) if options.request_stdin
                      else parse_connection(connection_args))
        remaining = deadline - time.monotonic()
        if cancelled.is_set():
            raise AcquisitionError('cancelled')
        if remaining <= 0:
            raise AcquisitionError('timeout')
        schema = acquire_schema(connection, executable=options.csql, timeout=remaining, cancelled=cancelled)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AcquisitionError('timeout')
        output = snapshot_json(schema, source=connection, timeout=remaining, cancelled=cancelled)
        if cancelled.is_set():
            raise AcquisitionError('cancelled')
        if time.monotonic() >= deadline:
            raise AcquisitionError('timeout')
        sys.stdout.write(output)
        return 0
    except AcquisitionError as error:
        sys.stderr.write(f'cubrid-schema: {error}\n')
        return {'invalid-request': 2, 'timeout': 124, 'cancelled': 130}.get(error.code, 3)
    except (OSError, ValueError, RecursionError):
        sys.stderr.write('cubrid-schema: Schema export failed.\n')
        return 3
    finally:
        for sig, previous in handlers.items():
            signal.signal(sig, previous)


if __name__ == '__main__':
    sys.exit(main())

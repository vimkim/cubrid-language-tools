"""Explicit, bounded CSQL catalog acquisition outside the offline language core."""

from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import re
import selectors
import shlex
import shutil
import signal
import subprocess
import tempfile
from threading import Event
import time
from typing import Sequence

from .models import Relation, Schema


MAX_CATALOG_BYTES = 16 * 1024 * 1024
MAX_REQUEST_BYTES = 64 * 1024
MAX_TIMEOUT = 300
CATALOG_QUERY = """
SELECT 'identity' AS kind, CURRENT_USER AS login_name, CURRENT_USER AS owner_name,
       DATABASE() AS class_name, DATABASE() AS item_name, 'DATABASE' AS item_type
FROM db_root
UNION ALL
SELECT CASE WHEN is_system_class = 'YES' THEN 'system' ELSE 'relation' END,
       CURRENT_USER, owner_name, class_name, class_name, class_type
FROM db_class
UNION ALL
SELECT 'column', CURRENT_USER, a.owner_name, a.class_name, a.attr_name, a.attr_type
FROM db_attribute a JOIN db_class c
ON a.owner_name = c.owner_name AND a.class_name = c.class_name
WHERE a.attr_type IN ('INSTANCE', 'SHARED')
UNION ALL
SELECT 'index', CURRENT_USER, owner_name, class_name, index_name, 'INDEX'
FROM db_index
UNION ALL
SELECT 'user', CURRENT_USER, CURRENT_USER, name, name, 'USER' FROM db_user;
"""
_HEADER = 'kind\tlogin_name\towner_name\tclass_name\titem_name\titem_type'
_MESSAGES = {
    'invalid-request': 'Invalid schema export request or options.',
    'unavailable': 'CSQL schema acquisition is unavailable.',
    'platform': 'Schema acquisition requires POSIX process groups.',
    'failed': 'CSQL schema acquisition failed.',
    'catalog': 'CSQL returned invalid catalog metadata.',
    'limit': 'Schema acquisition exceeded its output limit.',
    'timeout': 'Schema acquisition deadline exceeded.',
    'cancelled': 'Schema acquisition cancelled.',
}
_ENDPOINT = re.compile(r'[\w.-]+(?:@(?:[\w.-]+|\[[0-9a-fA-F:]+\])(?::[0-9]{1,5})?)?\Z')


class AcquisitionError(Exception):
    """A fixed, redacted failure category safe for caller diagnostics."""

    def __init__(self, code: str):
        self.code = code if code in _MESSAGES else 'failed'
        super().__init__(_MESSAGES[self.code])


def _valid_text(value: object, *, empty: bool = False) -> bool:
    if not isinstance(value, str) or (not empty and not value) or '\0' in value:
        return False
    try:
        value.encode('utf-8')
        return True
    except UnicodeError:
        return False


@dataclass(frozen=True)
class Connection:
    """Validated connection fields. Repr omits all connection details."""

    endpoint: str = field(repr=False)
    user: str | None = field(default=None, repr=False)
    password: str = field(default='', repr=False, compare=False)

    def __post_init__(self):
        if (not _valid_text(self.endpoint) or not _ENDPOINT.fullmatch(self.endpoint)
                or self.endpoint.startswith('-')
                or (self.user is not None and (not _valid_text(self.user)
                                               or self.user.startswith('-')
                                               or any(ord(c) < 32 for c in self.user)))
                or not _valid_text(self.password, empty=True)):
            raise AcquisitionError('invalid-request')
        if sum(len(value.encode('utf-8')) for value in
               (self.endpoint, self.user or '', self.password)) > MAX_REQUEST_BYTES:
            raise AcquisitionError('invalid-request')


def parse_connection(command: str | Sequence[str], *, password: str | None = None) -> Connection:
    """Parse CSQL connection arguments without shell expansion or execution.

    A leading csql token is descriptive. Only acquire_schema's executable selects
    the program. A non-None password overrides any inline password.
    """
    if password is not None and not _valid_text(password, empty=True):
        raise AcquisitionError('invalid-request')
    if isinstance(command, str):
        if not _valid_text(command) or len(command.encode('utf-8')) > MAX_REQUEST_BYTES:
            raise AcquisitionError('invalid-request')
        try:
            tokens = shlex.split(command)
        except ValueError:
            raise AcquisitionError('invalid-request') from None
    elif isinstance(command, (list, tuple)):
        tokens = list(command)
    else:
        raise AcquisitionError('invalid-request')
    if (not tokens or any(not _valid_text(token, empty=True) for token in tokens)
            or sum(len(token.encode('utf-8')) for token in tokens) > MAX_REQUEST_BYTES):
        raise AcquisitionError('invalid-request')
    if Path(tokens[0]).name == 'csql':
        tokens.pop(0)
    values: dict[str, str] = {}
    endpoint = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if token in ('-C', '--CS-mode'):
            continue
        field_name = None
        value = None
        if token in ('-u', '--user', '-p', '--password'):
            field_name = 'user' if token in ('-u', '--user') else 'password'
            if index == len(tokens):
                raise AcquisitionError('invalid-request')
            value = tokens[index]
            index += 1
            if value.startswith('-'):
                raise AcquisitionError('invalid-request')
        elif token.startswith(('--user=', '--password=')):
            field_name, value = token[2:].split('=', 1)
        elif token.startswith(('-u', '-p')) and not token.startswith('--'):
            field_name = 'user' if token[1] == 'u' else 'password'
            value = token[2:]
        elif token.startswith('-') or endpoint is not None:
            raise AcquisitionError('invalid-request')
        else:
            endpoint = token
        if field_name is not None:
            if field_name in values and values[field_name] != value:
                raise AcquisitionError('invalid-request')
            values[field_name] = value
    if endpoint is None:
        raise AcquisitionError('invalid-request')
    return Connection(endpoint, values.get('user'), password if password is not None else values.get('password', ''))


def validate_timeout(timeout: float) -> float:
    """Validate the shared CLI and importable acquisition deadline bound."""
    if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
            or not 0 < timeout <= MAX_TIMEOUT or not math.isfinite(timeout)):
        raise AcquisitionError('invalid-request')
    return float(timeout)


def _check_deadline(deadline: float, cancelled: Event | None) -> None:
    if cancelled is not None and cancelled.is_set():
        raise AcquisitionError('cancelled')
    if time.monotonic() >= deadline:
        raise AcquisitionError('timeout')


def _kill_group(process: subprocess.Popen) -> None:
    # The leader may have exited while descendants still hold its pipes.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def acquire_schema(connection: Connection, *, executable: str = 'csql', timeout: float = 5,
                   cancelled: Event | None = None) -> Schema:
    """Read visible metadata with fixed SQL and an owned, bounded POSIX child.

    The caller owns refresh scheduling and supplies an optional cancellation Event.
    The environment is inherited. CSQL receives its actual batch password in argv.
    """
    deadline = time.monotonic() + validate_timeout(timeout)
    if not isinstance(connection, Connection) or not _valid_text(executable):
        raise AcquisitionError('invalid-request')
    _check_deadline(deadline, cancelled)
    if os.name != 'posix':
        raise AcquisitionError('platform')
    try:
        program = shutil.which(executable)
        if program is None:
            raise AcquisitionError('unavailable')
        program = str(Path(program).resolve())
        arguments = [program, '-C', '-p', connection.password, '-r', '-t', '-c', CATALOG_QUERY]
        if connection.user is not None:
            arguments.extend(('-u', connection.user))
        arguments.append(connection.endpoint)
        with tempfile.TemporaryDirectory(prefix='cubrid-schema-') as directory:
            _check_deadline(deadline, cancelled)
            process = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, start_new_session=True, cwd=directory)
            try:
                output = bytearray()
                total = 0
                has_stderr = False
                with selectors.DefaultSelector() as selector:
                    for stream in (process.stdout, process.stderr):
                        os.set_blocking(stream.fileno(), False)
                        selector.register(stream, selectors.EVENT_READ)
                    while selector.get_map() or process.poll() is None:
                        _check_deadline(deadline, cancelled)
                        if process.poll() is not None:
                            _kill_group(process)
                        for key, _ in selector.select(min(.02, max(0, deadline - time.monotonic()))):
                            chunk = os.read(key.fd, min(65536, MAX_CATALOG_BYTES - total + 1))
                            if not chunk:
                                selector.unregister(key.fileobj)
                                continue
                            total += len(chunk)
                            if total > MAX_CATALOG_BYTES:
                                raise AcquisitionError('limit')
                            if key.fileobj is process.stdout:
                                output.extend(chunk)
                            else:
                                has_stderr = True
                _check_deadline(deadline, cancelled)
                if process.returncode != 0 or has_stderr:
                    raise AcquisitionError('failed')
                schema = _parse_catalog(bytes(output), connection.endpoint.split('@', 1)[0], deadline, cancelled)
                _check_deadline(deadline, cancelled)
                return schema
            finally:
                _kill_group(process)
                process.stdout.close()
                process.stderr.close()
                process.wait()
    except (OSError, ValueError, subprocess.SubprocessError):
        raise AcquisitionError('unavailable') from None


def _unescape(value: str, deadline: float, cancelled: Event | None) -> str:
    if '\\' not in value:
        return value
    result = []
    index = 0
    next_check = 0
    escapes = {'n': '\n', 't': '\t', '\\': '\\'}
    while index < len(value):
        if index >= next_check:
            _check_deadline(deadline, cancelled)
            next_check = index + 65536
        character = value[index]
        if character == '\\':
            index += 1
            if index == len(value) or value[index] not in escapes:
                raise AcquisitionError('catalog')
            character = escapes[value[index]]
        result.append(character)
        index += 1
    return ''.join(result)


def _parse_catalog(output: bytes, database: str, deadline: float, cancelled: Event | None) -> Schema:
    try:
        text = output.decode('utf-8')
    except UnicodeError:
        raise AcquisitionError('catalog') from None
    if '\0' in text or not text.endswith('\n'):
        raise AcquisitionError('catalog')
    lines = text.rstrip('\n').split('\n')
    if lines.pop(0) != _HEADER:
        raise AcquisitionError('catalog')
    identity = None
    logins = set()
    relations = {}
    columns: dict[tuple[str, str], set[str]] = {}
    indexes: dict[tuple[str, str], set[str]] = {}
    users = set()
    for line in lines:
        _check_deadline(deadline, cancelled)
        fields = [_unescape(field, deadline, cancelled) for field in line.split('\t')]
        if len(fields) != 6 or any(not field for field in fields):
            raise AcquisitionError('catalog')
        tag, login, owner, name, item, kind = fields
        logins.add(login)
        key = (owner, name)
        if tag == 'identity':
            if identity is not None or owner != login or name != database or item != database or kind != 'DATABASE':
                raise AcquisitionError('catalog')
            identity = login
        elif tag in ('relation', 'system'):
            if kind not in ('CLASS', 'VCLASS') or key in relations or item != name:
                raise AcquisitionError('catalog')
            relations[key] = (kind, tag == 'system')
        elif tag == 'column' and kind in ('INSTANCE', 'SHARED'):
            columns.setdefault(key, set()).add(item)
        elif tag == 'index' and kind == 'INDEX':
            indexes.setdefault(key, set()).add(item)
        elif tag == 'user' and kind == 'USER' and owner == login and name == item:
            users.add(item)
        else:
            raise AcquisitionError('catalog')
    if (identity is None or logins != {identity}
            or columns.keys() - relations.keys() or indexes.keys() - relations.keys()):
        raise AcquisitionError('catalog')
    order = lambda name: (name.casefold(), name)
    return Schema(identity, tuple(
        Relation(owner, name, kind, tuple(sorted(columns.get((owner, name), ()), key=order)), system,
                 tuple(sorted(indexes.get((owner, name), ()), key=order)))
        for (owner, name), (kind, system) in sorted(relations.items())
    ), tuple(sorted(users, key=order)), database)


def snapshot_json(schema: Schema, *, source: Connection | None = None, timeout: float = 5,
                  cancelled: Event | None = None) -> str:
    """Encode metadata as a size-bounded version 1 snapshot with an optional endpoint."""
    deadline = time.monotonic() + validate_timeout(timeout)
    _check_deadline(deadline, cancelled)
    data = {
        'schemaVersion': 1, 'user': schema.user, 'database': schema.database,
        'relations': [dict(owner=r.owner, name=r.name, kind=r.kind, columns=r.columns,
                           system=r.system, indexes=r.indexes) for r in schema.relations],
        'users': schema.users,
    }
    if source is not None:
        data['source'] = {'endpoint': source.endpoint}
    encoded = []
    size = 1
    for chunk in json.JSONEncoder(ensure_ascii=False, separators=(',', ':')).iterencode(data):
        _check_deadline(deadline, cancelled)
        size += len(chunk.encode('utf-8'))
        if size > MAX_CATALOG_BYTES:
            raise AcquisitionError('limit')
        encoded.append(chunk)
    return ''.join(encoded) + '\n'

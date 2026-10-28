"""Shared loading and explicit refresh of offline schema metadata."""

from dataclasses import dataclass
import json
from pathlib import Path

from .models import Relation, Schema


@dataclass(frozen=True)
class SchemaSnapshot:
    """An immutable load result shared by CLI and LSP callers.

    Adapters pass ``schema`` to completion and display ``availability`` when set.
    ``stale`` means that refresh failed and ``schema`` is the last valid metadata.
    """

    schema: Schema | None
    availability: str | None = None
    stale: bool = False


def load_snapshot(path: str | Path | None) -> SchemaSnapshot:
    """Read UTF-8 JSON from a caller-resolved path without consulting configuration.

    ``None`` means no snapshot is configured. A read or validation failure returns
    no schema and an availability message. Unknown JSON fields are ignored.
    """
    if path is None:
        return SchemaSnapshot(None, 'Schema snapshot not configured; keyword completion remains available.')
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        return SchemaSnapshot(_parse_schema(data))
    except (OSError, ValueError, RecursionError) as error:
        return SchemaSnapshot(None, f'Schema snapshot unavailable at {path}: {error}')


def refresh_snapshot(path: str | Path | None, previous: SchemaSnapshot) -> SchemaSnapshot:
    """Read after an explicit refresh or configuration event.

    A failed read retains ``previous.schema`` and marks it stale. A successful
    read clears stale state. ``None`` explicitly disables schema metadata.
    The caller owns paths, refresh scheduling, and the returned state.
    """
    current = load_snapshot(path)
    if path is not None and current.schema is None and previous.schema is not None:
        return SchemaSnapshot(
            previous.schema,
            f'Schema snapshot is stale; retaining last valid metadata. {current.availability}',
            stale=True,
        )
    return current


def _string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f'{field} must be a string')
    return value


def _list(value: object, field: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f'{field} must be a list')
    return value


def _string_list(value: object, field: str) -> list[str]:
    values = _list(value, field)
    if any(not isinstance(item, str) for item in values):
        raise ValueError(f'{field} must contain only strings')
    return values


def _parse_schema(data: object) -> Schema:
    if not isinstance(data, dict):
        raise ValueError('snapshot must be an object')
    if type(data.get('schemaVersion')) is not int or data['schemaVersion'] != 1:
        raise ValueError('schemaVersion must be integer 1')
    user = _string(data.get('user'), 'user')
    relations = []
    for index, relation in enumerate(_list(data.get('relations'), 'relations')):
        field = f'relations[{index}]'
        if not isinstance(relation, dict):
            raise ValueError(f'{field} must be an object')
        owner = _string(relation.get('owner'), f'{field}.owner')
        name = _string(relation.get('name'), f'{field}.name')
        kind = _string(relation.get('kind'), f'{field}.kind')
        if kind not in ('CLASS', 'VCLASS'):
            raise ValueError(f'{field}.kind must be CLASS or VCLASS')
        columns = _string_list(relation.get('columns'), f'{field}.columns')
        system = relation.get('system', False)
        if type(system) is not bool:
            raise ValueError(f'{field}.system must be a boolean')
        indexes = _string_list(relation.get('indexes', []), f'{field}.indexes')
        relations.append(Relation(owner, name, kind, columns, system, indexes))
    users = _string_list(data.get('users', []), 'users')
    database = _string(data.get('database', ''), 'database')
    return Schema(user, relations, users, database)

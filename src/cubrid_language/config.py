"""Metadata-only project configuration shared by command-line and LSP callers."""

from dataclasses import dataclass
import json
import os
from pathlib import Path

from .validation.models import PROFILE

_UNSET = object()


class ConfigError(ValueError):
    code = 'CUBRID-T1003'


def _text(value):
    if not isinstance(value, str) or not value.strip() or '\0' in value:
        return False
    try:
        value.encode('utf-8', errors='strict')
        return True
    except UnicodeError:
        return False


def _fields(values):
    if not isinstance(values, dict):
        raise ConfigError('project configuration must be a JSON object')
    if set(values) - {'profile', 'scriptMode', 'schemaSnapshot'}:
        raise ConfigError('project configuration permits only profile, scriptMode, and schemaSnapshot')
    if 'profile' in values and not _text(values['profile']):
        raise ConfigError('profile must be a nonempty Unicode string')
    if 'scriptMode' in values and values['scriptMode'] not in ('sql', 'csql'):
        raise ConfigError('scriptMode must be sql or csql')
    if 'schemaSnapshot' in values and values['schemaSnapshot'] is not None and not _text(values['schemaSnapshot']):
        raise ConfigError('schemaSnapshot must be a nonempty Unicode path or null')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError('duplicate configuration keys are invalid')
        result[key] = value
    return result


@dataclass(frozen=True)
class ResolvedConfig:
    profile: str
    script_mode: str
    schema_snapshot: Path | None = None


def _absolute(path, base):
    value = Path(path)
    return Path(os.path.abspath(value if value.is_absolute() else base / value))


def _load(path):
    try:
        values = json.loads(path.read_bytes().decode('utf-8', errors='strict'), object_pairs_hook=_unique_object)
        _fields(values)
        if 'schemaSnapshot' in values and values['schemaSnapshot'] is not None:
            values['schemaSnapshot'] = _absolute(values['schemaSnapshot'], path.parent)
        return values
    except (OSError, ValueError, RecursionError) as error:
        raise ConfigError(f'cannot load project configuration {path}: {error}') from error


def _resolve_config(document_path=None, *, cwd=None, config_path=None, profile=None,
                   script_mode=None, schema_snapshot=_UNSET):
    """Resolve fields in caller, explicit-file, nearest-file, default order.

    Omit schema_snapshot to inherit metadata. Pass None to disable it. Relative
    caller paths use cwd. A file's snapshot paths use that file's directory.
    Stdin/untitled callers pass document_path=None for discovery from cwd.
    """
    base = _absolute(cwd, Path.cwd()) if cwd is not None else Path.cwd()
    document = _absolute(document_path, base) if document_path is not None else None
    origin = document.parent if document is not None else base
    values = {'profile': PROFILE,
              'scriptMode': 'csql' if document is not None and document.suffix.lower() == '.csql' else 'sql',
              'schemaSnapshot': None}
    for ancestor in (origin, *origin.parents):
        candidate = ancestor / '.cubrid-language.json'
        try:
            candidate.lstat()
        except FileNotFoundError:
            continue
        values.update(_load(candidate))
        break
    if config_path is not None:
        values.update(_load(_absolute(config_path, base)))
    if profile is not None:
        values['profile'] = profile
    if script_mode is not None:
        values['scriptMode'] = script_mode
    if schema_snapshot is not _UNSET:
        values['schemaSnapshot'] = None if schema_snapshot is None else _absolute(schema_snapshot, base)
    return ResolvedConfig(values['profile'], values['scriptMode'], values['schemaSnapshot'])


def resolve_config(document_path=None, *, cwd=None, config_path=None, profile=None,
                   script_mode=None, schema_snapshot=_UNSET):
    """Resolve metadata per field. An omitted snapshot inherits, None disables.

    Explicit caller values override the explicit config file, the nearest
    ancestor config, then defaults. Each file resolves its own relative snapshot
    paths. Relative caller paths use cwd. Stdin/untitled documents pass None.
    Invalid supplied configuration raises ConfigError with code CUBRID-T1003.
    """
    overrides = {}
    if profile is not None:
        overrides['profile'] = profile
    if script_mode is not None:
        overrides['scriptMode'] = script_mode
    if schema_snapshot is not _UNSET:
        overrides['schemaSnapshot'] = str(schema_snapshot) if isinstance(schema_snapshot, Path) else schema_snapshot
    _fields(overrides)
    try:
        return _resolve_config(document_path, cwd=cwd, config_path=config_path, profile=profile,
                               script_mode=script_mode, schema_snapshot=schema_snapshot)
    except (OSError, ValueError, TypeError, RecursionError) as error:
        if isinstance(error, ConfigError):
            raise
        raise ConfigError(f'cannot resolve project configuration: {error}') from error

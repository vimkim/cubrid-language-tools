"""Optional pygls transport for the shared language interfaces."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
import threading
from pathlib import Path
from urllib.parse import unquote, urlsplit

from cattrs.errors import ClassValidationError
from lsprotocol import types
from pygls.exceptions import JsonRpcInvalidParams
from pygls.lsp.server import LanguageServer
from pygls.protocol import LanguageServerProtocol, default_converter
from pygls.protocol.language_server import lsp_method

from . import complete
from .config import ConfigError, ResolvedConfig, resolve_config
from .schema import SchemaSnapshot, load_snapshot, refresh_snapshot
from .validation import PROFILE, Validator, WorkerConfig
from .validation.positions import DocumentMap


@dataclass
class Document:
    text: str
    version: int
    config: ResolvedConfig | None = None
    error: str | None = None
    job: 'ValidationJob | None' = None
    snapshot: SchemaSnapshot | None = None


class ValidationJob:
    """A cancellation gate also covers work still queued in the executor."""

    def __init__(self, worker_config):
        self.validator = Validator(worker_config)
        self.cancelled = threading.Event()
        self.task = None
        self.closing = False

    def run(self, text, config):
        if not self.cancelled.is_set():
            return self.validator.validate(text, config.profile, config.script_mode)


class Adapter:
    def __init__(self, server):
        self.server = server
        self.documents = {}
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='cubrid-validation')
        self.cleanups = set()
        self.stopped = False
        self.settings = {}
        self.settings_error = None
        self.worker_config = None
        self.cwd = Path.cwd()
        self.epoch = 0

    def settings_changed(self, settings):
        self.epoch += 1
        try:
            if not isinstance(settings, dict):
                raise ConfigError('language-server settings must be an object')
            values = settings.get('cubrid', {})
            allowed = {'profile', 'scriptMode', 'schemaSnapshot', 'configPath', 'parserWorker',
                       'runtimePrefix', 'workerManifest', 'workerTimeout'}
            if not isinstance(values, dict) or set(values) - allowed:
                raise ConfigError('cubrid settings contain unknown fields or are not an object')
            if any(values[key] is None for key in ('profile', 'scriptMode', 'configPath') if key in values):
                raise ConfigError('only schemaSnapshot can clear metadata with null')
            worker = None
            if set(values) & {'parserWorker', 'runtimePrefix', 'workerManifest', 'workerTimeout'}:
                if not all(isinstance(values.get(k), str) and values[k] for k in ('parserWorker', 'runtimePrefix')):
                    raise ConfigError('trusted parserWorker and runtimePrefix must both be configured')
                for key in ('parserWorker', 'runtimePrefix', 'workerManifest'):
                    if key in values and values[key] is not None:
                        value = values[key]
                        if not isinstance(value, str) or not value or '\0' in value:
                            raise ConfigError(f'{key} must be a nonempty Unicode path without NUL')
                        value.encode('utf-8', errors='strict')
                worker = WorkerConfig(Path(values['parserWorker']), Path(values['runtimePrefix']),
                    manifest=Path(values['workerManifest']) if values.get('workerManifest') is not None else None,
                    timeout=values.get('workerTimeout', 5.0))
            self.settings, self.worker_config, self.settings_error = dict(values), worker, None
        except (ConfigError, ValueError, TypeError) as error:
            self.settings, self.worker_config, self.settings_error = {}, None, str(error)

    def stop_job(self, job):
        if job is None or job.closing:
            return
        job.closing = True
        job.cancelled.set()
        if job.task is not None:
            job.task.cancel()
        # A separate executor keeps close responsive even if parsing is queued.
        future = asyncio.get_running_loop().run_in_executor(None, job.validator.close)
        self.cleanups.add(future)
        future.add_done_callback(self.cleanups.discard)

    def stop_jobs(self, jobs):
        jobs = [job for job in jobs if job is not None]
        # Gate every queued start before cleanup can free a validation thread.
        for job in jobs:
            job.cancelled.set()
        for job in jobs:
            self.stop_job(job)

    def schedule(self, uri, document):
        self.stop_job(document.job)
        if self.stopped:
            return
        job = ValidationJob(self.worker_config)
        document.job = job
        job.task = asyncio.create_task(self.diagnose(uri, document, job))

    async def diagnose(self, uri, document, job):
        text, version, config = document.text, document.version, document.config
        error = document.error
        try:
            await asyncio.sleep(0.25)
            if error:
                diagnostics = [tool_diagnostic('CUBRID-T1003', error)]
            else:
                result = await asyncio.get_running_loop().run_in_executor(self.executor, job.run, text, config)
                if result is None:
                    return
                diagnostics = []
                try:
                    mapping = DocumentMap(text)
                except ValueError:
                    mapping = None
                for value in result.diagnostics:
                    if mapping is None:
                        diagnostics.append(tool_diagnostic('CUBRID-T1003', value.message))
                        continue
                    try:
                        location = protocol_range(mapping, value.span)
                    except ValueError:
                        diagnostics.append(tool_diagnostic('CUBRID-T1002',
                            'Validation returned a range outside protocol text positions.'))
                        continue
                    diagnostics.append(types.Diagnostic(location, message=value.message, code=value.code,
                        severity=types.DiagnosticSeverity.Error if value.severity == 'error'
                        else types.DiagnosticSeverity.Warning, source='cubrid',
                        data={'category': value.category, 'rangePrecision': value.range_precision}))
            if (not self.stopped and not job.cancelled.is_set() and self.documents.get(uri) is document
                    and document.job is job and document.version == version):
                self.server.text_document_publish_diagnostics(types.PublishDiagnosticsParams(
                    uri=uri, version=version, diagnostics=diagnostics))
        finally:
            # Do not cancel the coroutine currently running its own cleanup.
            job.task = None
            self.stop_job(job)

    def resolve(self, uri, previous):
        try:
            if self.settings_error:
                raise ConfigError(self.settings_error)
            parsed = urlsplit(uri)
            path = unquote(parsed.path) if parsed.scheme == 'file' and not parsed.netloc else None
            values = self.settings
            overrides = {'cwd': self.cwd, 'config_path': values.get('configPath'),
                         'profile': values.get('profile'),
                         'script_mode': values.get('scriptMode', 'sql' if path is None else None)}
            if 'schemaSnapshot' in values:
                overrides['schema_snapshot'] = values['schemaSnapshot']
            config = resolve_config(path, **overrides)
            snapshot = (load_snapshot(config.schema_snapshot) if previous is None
                        else refresh_snapshot(config.schema_snapshot, previous))
            return config, None, snapshot
        except (ConfigError, ValueError) as error:
            return None, str(error), previous or load_snapshot(None)

    def apply_configuration(self, uri, document, resolved):
        document.config, document.error, document.snapshot = resolved
        message = document.error or (document.snapshot.availability if document.config
                                    and document.config.schema_snapshot is not None else None)
        if message:
            self.server.window_log_message(types.LogMessageParams(
                type=types.MessageType.Warning, message=f'{uri}: {message}'))

    def configure(self, uri, document):
        self.apply_configuration(uri, document, self.resolve(uri, document.snapshot))

    def state(self, uri, document):
        return {'uri': uri, 'profile': document.config.profile if document.config else None,
                'scriptMode': document.config.script_mode if document.config else None,
                'schemaAvailable': document.snapshot.schema is not None,
                'stale': document.snapshot.stale, 'availability': document.error or document.snapshot.availability}

    async def shutdown(self):
        self.stopped = True
        tasks = [d.job.task for d in self.documents.values() if d.job is not None and d.job.task is not None]
        self.stop_jobs(document.job for document in self.documents.values())
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if self.cleanups:
            await asyncio.gather(*self.cleanups)
        await asyncio.get_running_loop().run_in_executor(None, self.executor.shutdown)

    def finish(self):
        """EOF/exit fallback, called after the protocol event loop has stopped."""
        self.stopped = True
        for document in self.documents.values():
            if document.job is not None:
                document.job.cancelled.set()
        for document in self.documents.values():
            if document.job is not None:
                document.job.validator.close()
        self.executor.shutdown(wait=True, cancel_futures=True)


class CubridServer(LanguageServer):
    def shutdown(self):
        self.adapter.finish()
        super().shutdown()


def protocol_range(mapping, span):
    return types.Range(types.Position(*mapping.to_position(span.start)),
                       types.Position(*mapping.to_position(span.end)))


def tool_diagnostic(code, message):
    return types.Diagnostic(types.Range(types.Position(0, 0), types.Position(0, 0)),
        message=message, code=code, severity=types.DiagnosticSeverity.Error,
        source='cubrid', data={'category': 'tool', 'rangePrecision': 'statement'})


class Utf16Protocol(LanguageServerProtocol):
    def structure_message(self, data):
        if 'jsonrpc' not in data or 'method' not in data:
            return super().structure_message(data)
        try:
            message_type = self.get_message_type(data['method'])
            if message_type is not None:
                # Convert known LSP messages before pygls's traceback/log path.
                return self._converter.structure(data, message_type)
            return super().structure_message(data)
        except (ClassValidationError, TypeError, ValueError, JsonRpcInvalidParams):
            error = JsonRpcInvalidParams(f'Invalid parameters for {data["method"]}')
            if 'id' in data:
                self._send_response(data['id'], error=error.to_response_error())
            else:
                self._server.window_log_message(types.LogMessageParams(
                    type=types.MessageType.Error, message=error.message))
            return None

    def handle_message(self, message):
        if message is not None:
            super().handle_message(message)

    @lsp_method(types.INITIALIZE)
    def lsp_initialize(self, params):
        # This must run before pygls creates its Workspace, not in a feature hook.
        if params.capabilities.general is None:
            params.capabilities.general = types.GeneralClientCapabilities()
        params.capabilities.general.position_encodings = [types.PositionEncodingKind.Utf16]
        return (yield from super().lsp_initialize(params))

    @lsp_method(types.TEXT_DOCUMENT_DID_CHANGE)
    def lsp_text_document__did_change(self, params):
        if any(getattr(change, 'range', None) is not None for change in params.content_changes):
            self._server.window_log_message(types.LogMessageParams(
                type=types.MessageType.Error, message='Full synchronization requires whole-document changes.'))
            return
        yield from super().lsp_text_document__did_change(params)


def strict_converter():
    converter = default_converter()

    def primitive(value, expected):
        wire_type = (int if issubclass(expected, int) else str) if issubclass(expected, Enum) else expected
        if type(value) is not wire_type:
            raise ValueError(f'expected {wire_type.__name__}, received {type(value).__name__}')
        return expected(value) if issubclass(expected, Enum) else value

    converter.register_structure_hook(int, primitive)
    converter.register_structure_hook(str, primitive)
    return converter


def create_server():
    server = CubridServer('cubrid-language-tools', '0.1.0.dev0',
                            text_document_sync_kind=types.TextDocumentSyncKind.Full,
                            protocol_cls=Utf16Protocol, converter_factory=strict_converter)
    adapter = Adapter(server)
    server.adapter = adapter
    server.exit_status = 1
    documents = adapter.documents

    @server.feature(types.INITIALIZE)
    def initialize(params):
        if params.root_uri:
            root = urlsplit(params.root_uri)
            if root.scheme == 'file' and not root.netloc:
                adapter.cwd = Path(unquote(root.path))
        adapter.settings_changed(params.initialization_options or {})

    @server.feature(types.INITIALIZED)
    def initialized(params):
        pass

    @server.feature(types.WORKSPACE_DID_CHANGE_CONFIGURATION)
    def configuration_changed(params):
        adapter.stop_jobs(document.job for document in documents.values())
        adapter.settings_changed(params.settings)
        for uri, document in documents.items():
            adapter.configure(uri, document)
            adapter.schedule(uri, document)

    @server.feature(types.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params):
        document = params.text_document
        previous = documents.pop(document.uri, None)
        if previous is not None:
            adapter.stop_job(previous.job)
            server.text_document_publish_diagnostics(types.PublishDiagnosticsParams(
                uri=document.uri, version=previous.version, diagnostics=[]))
        if document.language_id == 'cubrid':
            documents[document.uri] = Document(document.text, document.version)
            adapter.configure(document.uri, documents[document.uri])
            adapter.schedule(document.uri, documents[document.uri])

    @server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params):
        document = documents.get(params.text_document.uri)
        if document is not None and params.text_document.version > document.version:
            if params.content_changes:
                document.text = params.content_changes[-1].text
                document.version = params.text_document.version
                adapter.schedule(params.text_document.uri, document)

    @server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
    def did_close(params):
        document = documents.pop(params.text_document.uri, None)
        if document is not None:
            adapter.stop_job(document.job)
            server.text_document_publish_diagnostics(types.PublishDiagnosticsParams(
                uri=params.text_document.uri, version=document.version, diagnostics=[]))

    @server.feature(types.TEXT_DOCUMENT_COMPLETION)
    async def completion(params):
        await asyncio.sleep(0)
        document = documents.get(params.text_document.uri)
        if document is None:
            return types.CompletionList(is_incomplete=False, items=[])
        try:
            mapping = DocumentMap(document.text)
            cursor = mapping.from_position(params.position.line, params.position.character)
            result = complete(document.text, cursor, document.config.profile if document.config else PROFILE,
                              document.snapshot.schema)
            edit_range = protocol_range(mapping, result.replacement)
        except ValueError as error:
            raise JsonRpcInvalidParams(str(error)) from error
        return types.CompletionList(is_incomplete=False, items=[types.CompletionItem(
            label=item.label, detail=item.detail,
            text_edit=types.TextEdit(range=edit_range, new_text=item.text)) for item in result.items])

    @server.command('cubrid.reloadSchema')
    async def reload_schema(*args):
        states = []
        epoch = adapter.epoch
        for uri, document in list(documents.items()):
            resolved = await asyncio.get_running_loop().run_in_executor(None, adapter.resolve, uri, document.snapshot)
            if not adapter.stopped and adapter.epoch == epoch and documents.get(uri) is document:
                adapter.apply_configuration(uri, document, resolved)
                adapter.schedule(uri, document)
                states.append(adapter.state(uri, document))
        return states

    @server.feature(types.SHUTDOWN)
    async def shutdown(*args):
        await adapter.shutdown()
        server.exit_status = 0

    return server

"""A real Content-Length stdio client; stdout must contain protocol frames only."""

import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time


class Client:
    def __init__(self, cwd=None):
        environment = dict(os.environ)
        if 'PYTHONPATH' in environment:
            environment['PYTHONPATH'] = os.pathsep.join(str(Path(p).absolute())
                for p in environment['PYTHONPATH'].split(os.pathsep) if p)
        console = Path(sys.executable).with_name('cubrid-language-server')
        command = [str(console)] if console.exists() else [sys.executable, '-m', 'cubrid_language.lsp']
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, cwd=cwd, env=environment)
        self.messages = queue.Queue()
        self.pending = []
        self.next_id = 0
        self.shutdown_sent = False
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        try:
            while True:
                header = self.process.stdout.readline()
                if not header:
                    raise EOFError('server stdout ended')
                if not header.startswith(b'Content-Length: '):
                    raise AssertionError(f'non-protocol stdout: {header!r}')
                length = int(header.split(b':', 1)[1])
                while self.process.stdout.readline() != b'\r\n':
                    pass
                body = self.process.stdout.read(length)
                self.messages.put(json.loads(body))
        except BaseException as error:
            self.messages.put(error)

    def send(self, method, params=None, request=False):
        value = {'jsonrpc': '2.0', 'method': method}
        if params is not None:
            value['params'] = params
        if request:
            self.next_id += 1
            value['id'] = self.next_id
        body = json.dumps(value, ensure_ascii=True).encode('utf-8')
        self.process.stdin.write(f'Content-Length: {len(body)}\r\n\r\n'.encode() + body)
        self.process.stdin.flush()
        return value.get('id')

    def receive(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while True:
            for index, message in enumerate(self.pending):
                if predicate(message):
                    return self.pending.pop(index)
            value = self.messages.get(timeout=max(0.001, deadline - time.monotonic()))
            if isinstance(value, BaseException):
                raise value
            self.pending.append(value)

    def response(self, ident, timeout=5):
        return self.receive(lambda m: m.get('id') == ident, timeout)

    def request(self, method, params=None, timeout=5):
        response = self.response(self.send(method, params, request=True), timeout)
        if method == 'shutdown' and 'result' in response:
            self.shutdown_sent = True
        return response

    def initialize(self, settings=None, encodings=None):
        capabilities = {} if encodings is None else {'general': {'positionEncodings': encodings}}
        reply = self.request('initialize', {'processId': None, 'rootUri': None,
                                            'capabilities': capabilities,
                                            'initializationOptions': settings})
        self.send('initialized', {})
        return reply

    def open(self, text, uri='untitled:example', language='cubrid', version=1):
        self.send('textDocument/didOpen', {'textDocument': {'uri': uri, 'languageId': language,
                                                            'version': version, 'text': text}})
        return uri

    def change(self, uri, text, version=2):
        self.send('textDocument/didChange', {'textDocument': {'uri': uri, 'version': version},
                                            'contentChanges': [{'text': text}]})

    def completion(self, uri, line, character):
        return self.request('textDocument/completion', {'textDocument': {'uri': uri},
                                                        'position': {'line': line, 'character': character}})

    def diagnostics(self, uri, version=None, timeout=5):
        return self.receive(lambda m: m.get('method') == 'textDocument/publishDiagnostics'
                            and m['params']['uri'] == uri
                            and (version is None or m['params'].get('version') == version), timeout)['params']

    def close(self):
        if self.process.poll() is None:
            try:
                if not self.shutdown_sent:
                    self.request('shutdown', timeout=5)
                self.send('exit')
                self.process.wait(timeout=5)
            except (BrokenPipeError, EOFError, queue.Empty, subprocess.TimeoutExpired):
                self.process.kill()
                self.process.wait(timeout=5)
                raise
        self.reader.join(timeout=1)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

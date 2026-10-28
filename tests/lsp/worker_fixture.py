"""Explicit trusted child executables for protocol delays and failures."""

import hashlib
import json
import os
from pathlib import Path
import time

from cubrid_language.validation import PROFILE
from cubrid_language.validation.profiles import qualified_identity


def worker(root, initialize_delay=0, parse_delay=0, crash=False, bad_range=False):
    root = Path(root)
    manifest = root / 'manifest.json'
    manifest.write_text('{}')
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    prefix = root / 'runtime'
    identity = {'status': 'ready', 'manifestDigest': digest, **qualified_identity(PROFILE, prefix)}
    log = root / 'events.jsonl'
    executable = root / 'worker'
    executable.write_text("#!/usr/bin/python3\nimport json,os,sys,time\n"
        "print('trusted worker stderr probe',file=sys.stderr,flush=True)\n"
        f"identity={identity!r}\nlog={str(log)!r}\n"
        "def record(method):\n"
        " with open(log,'a') as stream: stream.write(json.dumps({'pid':os.getpid(),'method':method})+'\\n')\n"
        "for line in sys.stdin:\n"
        " request=json.loads(line)\n method=request['method']\n record(method)\n"
        f" if {crash!r}: raise SystemExit(9)\n"
        " if method=='initialize':\n"
        f"  time.sleep({initialize_delay!r})\n  result=dict(identity)\n"
        " elif method=='shutdown':\n  result={'status':'closed'}\n"
        " else:\n"
        f"  time.sleep({parse_delay!r})\n"
        "  result={'status':'valid','profile':identity['profile'],'coverage':'complete','diagnostics':[],"
        "'statementKinds':['PT_SELECT'],'manifestDigest':identity['manifestDigest'],'syntaxSettingsUnchanged':True,"
        "'coverageDecisions':[{'start':0,'end':len(request['text']),'admitted':True}],"
        "'nativeObservations':[{'hasTree':True,'treeCount':1,'hasError':False,'hasInternalError':False,"
        "'errorCount':0,'partialStackCount':0,'nativeErrorId':0}]}\n"
        f"  if {bad_range!r}:\n"
        "   result.update(status='syntax-error',statementKinds=[],diagnostics=[{'code':'CUBRID-S1001',"
        "'severity':'error','message':'invalid source range','span':{'start':1,'end':2},"
        "'rangePrecision':'exact','category':'syntax'}])\n"
        "   result['nativeObservations']=[{'hasTree':False,'treeCount':0,'hasError':True,"
        "'hasInternalError':False,'errorCount':1,'partialStackCount':0,'nativeErrorId':0}]\n"
        " result.update(protocolVersion=1,id=request['id'])\n print(json.dumps(result),flush=True)\n"
        " if method=='shutdown': break\n")
    executable.chmod(0o755)
    return {'cubrid': {'parserWorker': str(executable), 'runtimePrefix': str(prefix)}}, log


def event(log, method, count=1, timeout=4):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            values = [json.loads(line) for line in log.read_text().splitlines()]
            selected = [value for value in values if value['method'] == method]
            if len(selected) >= count:
                return selected[count - 1]
        except (OSError, ValueError):
            pass
        time.sleep(.01)
    raise AssertionError(f'worker event {method} #{count} not observed')


def wait_reaped(pid, timeout=2):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(.01)
    raise AssertionError(f'owned worker {pid} is still alive or unreaped')

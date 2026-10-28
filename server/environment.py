"""OpenEnv terminal wrapper. Agent commands run only inside Linux containers."""
import itertools
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import tempfile
import threading
import uuid
from openenv.core.env_server import Environment
from .models import Tbench2Action, Tbench2Observation, Tbench2State
from .tasks import TASKS,make_task
from .grading import grade_file

_IDS=itertools.count(20000)
_LOCK=threading.Lock()
RUNNER='/opt/reconcile-runner.py'

def kill_uid(uid):
    if uid is None: return
    # Repeat snapshots to catch children forked while the first sweep runs.
    for _ in range(4):
        found=False
        for item in Path('/proc').iterdir():
            if not item.name.isdecimal(): continue
            try:
                for line in (item/'status').read_text().splitlines():
                    if line.startswith('Uid:') and int(line.split()[1])==uid:
                        found=True
                        os.kill(int(item.name),signal.SIGKILL)
            except (OSError,ValueError,ProcessLookupError): pass
        if not found: break

class ReconcileEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS=True
    def __init__(self):
        super().__init__()
        self.workspace=None;self.uid=None;self._state=Tbench2State();self.last=None
    @property
    def state(self): return self._state
    def reset(self,seed=None,episode_id=None,task_id=None,**kwargs):
        task_id=task_id or TASKS[0]
        if task_id not in TASKS: raise ValueError('Unknown task_id')
        if not Path('/etc/reconcile-runtime').is_file() or os.getuid()!=0:
            raise RuntimeError('Run this environment in its Docker image; host shell execution is disabled')
        self.close()
        with _LOCK: self.uid=next(_IDS)
        self.workspace=Path(tempfile.mkdtemp(prefix='episode-',dir='/workspaces'))
        self.instruction,files,self.expected=make_task(task_id,seed if seed is not None else random.SystemRandom().randrange(2**63))
        for name,data in files.items():
            path=self.workspace/name;path.write_bytes(data);path.chmod(0o600);os.chown(path,self.uid,self.uid)
        self.workspace.chmod(0o700);os.chown(self.workspace,self.uid,self.uid)
        session=episode_id or str(uuid.uuid4())
        self._state=Tbench2State(task_id=task_id,episode_id=session,session_id=session,task_path=str(self.workspace),terminal_ready=True)
        self.last=self.observe('reset',f'Workspace: {self.workspace}. Start with ls or read instruction.txt.')
        return self.last
    def observe(self,action_type,output='',done=False,reward=0.0,success=True):
        return Tbench2Observation(instruction=self.instruction,output=output,done=done,reward=reward,
            success=success,task_id=self.state.task_id,task_path=str(self.workspace),session_id=self.state.session_id,
            action_type=action_type,info={'steps_remaining':max(0,32-self.state.step_count)})
    def run(self,kind,value,content=''):
        kill_uid(self.uid)
        with tempfile.TemporaryFile() as output:
            process=subprocess.Popen(['/usr/local/bin/python',RUNNER,str(self.uid),str(self.workspace),kind,value],
                stdin=subprocess.PIPE,stdout=output,stderr=subprocess.STDOUT,start_new_session=True,env={'PATH':'/usr/local/bin:/usr/bin:/bin'})
            timed_out=False
            try: process.communicate(input=content.encode(),timeout=15)
            except subprocess.TimeoutExpired:
                timed_out=True
                try: os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait(timeout=5)
            finally: kill_uid(self.uid)
            output.seek(0);data=output.read(16385)
            text=data[:16384].decode(errors='replace')
            if len(data)>16384:text+='\n[Output truncated at 16 KiB]'
            if timed_out:text+='\n[Command timed out after 15 seconds]'
            return text,process.returncode==0 and not timed_out
    def over_budget(self):
        total=0;entries=0
        for root,dirs,files in os.walk(self.workspace,followlinks=False):
            for name in dirs+files:
                entries+=1
                if entries>2048:return True
                try: total+=(Path(root)/name).lstat().st_size
                except OSError:continue
                if total>32*1024**2:return True
        return False
    def step(self,action:Tbench2Action,timeout_s=None,**kwargs):
        if self.last is None: raise RuntimeError('Reset first')
        if self.last.done:return self.last.model_copy(deep=True)
        self._state.step_count+=1
        kind=action.action_type;done=False;reward=0.0;success=True
        if len(action.command)>16384 or len(action.content.encode())>65536:
            output='Action exceeds command/content size limits.';success=False
        elif kind=='exec':output,success=self.run(kind,action.command)
        elif kind=='write_file':output,success=self.run(kind,action.file_path,action.content)
        elif kind in ('check','evaluate'):
            kill_uid(self.uid)
            success,output=grade_file(self.workspace,self.expected)
            done=kind=='evaluate';reward=float(success) if done else 0.0
        elif kind=='finish':output='Finished without evaluation.';done=True
        else: output='Unknown action_type. Use exec, write_file, check, evaluate or finish.';success=False
        if self.over_budget():done=True;reward=0.0;output='Workspace limit exceeded.';success=False
        if self.state.step_count>=32 and not done:
            kill_uid(self.uid);success,output=grade_file(self.workspace,self.expected);done=True;reward=float(success)
        self.last=self.observe(kind,output,done,reward,success)
        return self.last
    def close(self):
        if self.workspace is not None:
            kill_uid(self.uid);shutil.rmtree(self.workspace,ignore_errors=True)
        self.workspace=None;self.uid=None

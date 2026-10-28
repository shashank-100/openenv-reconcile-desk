"""Trusted Linux launcher. Drops privileges BEFORE any agent command runs."""
import ctypes
import os
import resource
import sys
uid=int(sys.argv[1]);workspace=sys.argv[2];kind=sys.argv[3]
os.chdir(workspace)
os.setgroups([])
os.setgid(uid);os.setuid(uid)
# A command cannot gain privileges through setuid binaries or file capabilities.
if ctypes.CDLL(None).prctl(38,1,0,0,0)!=0: raise RuntimeError('PR_SET_NO_NEW_PRIVS failed')
resource.setrlimit(resource.RLIMIT_CPU,(12,12))
resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_NPROC,(32,32))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.umask(0o077)
if kind=='exec':
    os.execve('/bin/sh',['/bin/sh','-c',sys.argv[4]],{'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':workspace,'TMPDIR':workspace,'LANG':'C.UTF-8','PYTHONNOUSERSITE':'1','OPENBLAS_NUM_THREADS':'1'})
elif kind=='write_file':
    from pathlib import Path
    path=Path(sys.argv[4])
    if path.is_absolute() or '..' in path.parts: raise ValueError('Use a relative workspace path')
    path.parent.mkdir(parents=True,exist_ok=True)
    # Any symlink traversal is still under the session UID, never privileged.
    path.write_text(sys.stdin.read(),encoding='utf-8')
else: raise ValueError('Unknown runner operation')

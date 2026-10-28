"""Reference and adversarial controls over the actual container's WebSocket."""
import asyncio
import json
from pathlib import Path
import sys
import websockets

TASKS=['source-spend','revised-payments','duplicate-exports','cancelled-payments','mixed-reconciliation']
SOLVER=Path(__file__).with_name('reference_solver.py').read_text()
async def exchange(ws,kind,data):
    await ws.send(json.dumps({'type':kind,'data':data}))
    response=json.loads(await ws.recv())
    assert response['type']=='observation',response
    return response['data']
async def action(ws,**kwargs):return await exchange(ws,'step',kwargs)
async def main(base):
    url=base.replace('http','ws',1)+'/ws';count=0
    for task in TASKS:
        for seed in [0,42,2026]:
            async with websockets.connect(url) as ws:
                initial=await exchange(ws,'reset',{'task_id':task,'seed':seed})
                assert initial['observation']['task_id']==task
                assert not initial['done']
                result=await action(ws,action_type='write_file',file_path='solve.py',content=SOLVER)
                assert result['observation']['success'],result
                result=await action(ws,action_type='exec',command='python3 solve.py')
                assert result['observation']['success'],result
                result=await action(ws,action_type='check')
                assert result['observation']['success'] and result['reward']==0 and not result['done'],result
                result=await action(ws,action_type='evaluate')
                assert result['done'] and result['reward']==1,result
                count+=1
            for mode in ['empty','nan','symlink','fifo']:
                async with websockets.connect(url) as ws:
                    await exchange(ws,'reset',{'task_id':task,'seed':seed})
                    if mode=='nan':
                        await action(ws,action_type='write_file',file_path='solve.py',content=SOLVER)
                        await action(ws,action_type='exec',command="python3 solve.py && python3 -c \"import csv; p='supplier_spend.csv'; r=list(csv.reader(open(p))); r[1][1]='NaN'; csv.writer(open(p,'w',newline='')).writerows(r)\"")
                    if mode=='symlink':await action(ws,action_type='exec',command='ln -s /etc/passwd supplier_spend.csv')
                    if mode=='fifo':await action(ws,action_type='exec',command='mkfifo supplier_spend.csv')
                    result=await action(ws,action_type='evaluate')
                    assert result['done'] and result['reward']==0,(task,mode,result)
                    count+=1
    # Session and grader isolation: agent A cannot read protected server code or B's files.
    async with websockets.connect(url) as a,websockets.connect(url) as b:
        ia=await exchange(a,'reset',{'task_id':'mixed-reconciliation','seed':1})
        ib=await exchange(b,'reset',{'task_id':'mixed-reconciliation','seed':2})
        path_b=ib['observation']['task_path']
        for command in ['cat /app/server/tasks.py',f'cat {path_b}/payments.csv','id -u']:
            result=await action(a,action_type='exec',command=command)
            if command=='id -u':assert int(result['observation']['output'].strip())>=20000
            else: assert not result['observation']['success'],result
        await action(a,action_type='write_file',file_path='../../outside',content='no')
        assert not (await action(a,action_type='exec',command='test -e ../../outside'))['observation']['success']
        result=await action(a,action_type='exec',command='sleep 60')
        assert not result['observation']['success'] and 'timed out' in result['observation']['output']
        result=await action(b,action_type='finish')
        assert result['done'] and result['reward']==0
    # Correct artifact also gets scored if the tool budget expires without evaluate.
    async with websockets.connect(url) as ws:
        await exchange(ws,'reset',{'task_id':'mixed-reconciliation','seed':1})
        await action(ws,action_type='write_file',file_path='solve.py',content=SOLVER)
        await action(ws,action_type='exec',command='python3 solve.py')
        for i in range(30):result=await action(ws,action_type='exec',command='true')
        assert result['done'] and result['reward']==1,result
    print(json.dumps({'native_episode_controls':count,'reference_solutions':15,'incorrect_output_controls':60,'isolation_timeout_budget':'PASS','result':'PASS'}))
asyncio.run(main(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8000'))

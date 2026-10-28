import csv
import hashlib
import io
import json
import re
from decimal import Decimal
from pathlib import Path
import pytest
from server.tasks import TASKS,make_task,HEADER,csv_text
from server.grading import grade_bytes,grade_file

ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'upstream').exists(): ROOT=Path('/app')

def independent_solution(files):
    names=files['suppliers.txt'].decode().splitlines()
    def key(name):
        return ' '.join(w for w in re.findall('[A-Z0-9]+',name.upper()) if w not in ['LTD','LIMITED','PLC','UK'])
    canonical={key(n):n for n in names}
    sums={n:{d:Decimal(0) for d in ['dwp','dbt','defra']} for n in names}
    if 'payments.csv' in files:
        newest={}
        for r in csv.DictReader(io.StringIO(files['payments.csv'].decode())):
            identity=r['record_id']
            if identity not in newest or int(r['revision'])>int(newest[identity]['revision']):newest[identity]=r
        for row in newest.values():
            if row['status']=='posted':sums[canonical[key(row['supplier'])]][row['department']]+=Decimal(row['amount'])
    else:
        for dept in ('dwp','dbt','defra'):
            for raw in csv.DictReader(io.StringIO(files[f'{dept}_spend_feb2026.csv'].decode('cp1252'))):
                r={k.strip():v for k,v in raw.items() if k}
                name=canonical.get(key(r.get('Supplier Name',r.get('Supplier',''))))
                if name is None:continue
                text=r.get('Transparency Invoice Amount',r.get('Amount',''))
                sums[name][dept]+=Decimal(text.strip().replace('£','').replace(',',''))
    return [[n,*[format(sums[n][d],'.2f') for d in ('dwp','dbt','defra')],format(sum(sums[n].values()),'.2f')] for n in names]

@pytest.mark.parametrize('task',TASKS)
@pytest.mark.parametrize('seed',[0,1,42,2026,999])
def test_reference_and_wrong_controls(task,seed):
    instruction,files,expected=make_task(task,seed)
    assert independent_solution(files)==expected
    good=csv_text(HEADER,expected).encode()
    assert grade_bytes(good,expected)[0]
    assert not grade_bytes(b'',expected)[0]
    altered=[r.copy() for r in expected];altered[0][1]=str(Decimal(altered[0][1])+Decimal('0.01'))
    assert not grade_bytes(csv_text(HEADER,altered).encode(),expected)[0]
    assert not grade_bytes(csv_text(HEADER,list(reversed(expected))).encode(),expected)[0]
    assert make_task(task,seed)==make_task(task,seed)

@pytest.mark.parametrize('value',['NaN','nan','Infinity','-Infinity','1e6','1,000.00','£1.00','0.000','+0.00'])
def test_nonfinite_and_bad_money(value):
    _,_,expected=make_task('source-spend',42)
    bad=[r.copy() for r in expected];bad[0][1]=value
    assert not grade_bytes(csv_text(HEADER,bad).encode(),expected)[0]

def test_baseline_matches_upstream_known_totals():
    _,_,expected=make_task('source-spend',0)
    values={r[0]:r[-1] for r in expected}
    # Numerical facts published with the original Pool Desk verifier.
    assert values['Accenture']=='6344045.03'
    assert values['Post Office']=='61131652.70'
    assert values['Softcat']=='7236230.05'
    assert values['WSP']=='1600447.54'

def test_original_files_unchanged():
    m=json.loads((ROOT/'upstream/manifest.json').read_text())
    for name,info in m['files'].items():
        assert hashlib.sha256((ROOT/'upstream'/name).read_bytes()).hexdigest()==info['sha256']

def test_seed_variation():
    for task in TASKS[1:]:
        assert make_task(task,1)[1]!=make_task(task,2)[1]
        assert make_task(task,1)[2]!=make_task(task,2)[2]

def test_shortcut_controls():
    for task in TASKS[1:]:
        _,files,wanted=make_task(task,42)
        rows=list(csv.DictReader(io.StringIO(files['payments.csv'].decode())))
        names=files['suppliers.txt'].decode().splitlines()
        def key(s):return ' '.join(w for w in re.findall('[A-Z0-9]+',s.upper()) if w not in ['LTD','LIMITED','PLC','UK'])
        canon={key(n):n for n in names}
        # Wrong shortcut: sum every export row, ignoring IDs, revisions and cancellation.
        totals={n:{d:Decimal(0) for d in ['dwp','dbt','defra']} for n in names}
        for r in rows:totals[canon[key(r['supplier'])]][r['department']]+=Decimal(r['amount'])
        bad=[[n,*[format(totals[n][d],'.2f') for d in ['dwp','dbt','defra']],format(sum(totals[n].values()),'.2f')] for n in names]
        assert not grade_bytes(csv_text(HEADER,bad).encode(),wanted)[0]

def test_safe_file_reader(tmp_path):
    _,_,expected=make_task('source-spend',0)
    path=tmp_path/'supplier_spend.csv'
    assert not grade_file(tmp_path,expected)[0]
    path.write_text(csv_text(HEADER,expected))
    assert grade_file(tmp_path,expected)[0]
    path.unlink();path.symlink_to('/etc/passwd')
    assert not grade_file(tmp_path,expected)[0]
    path.unlink()
    import os
    os.mkfifo(path)
    assert not grade_file(tmp_path,expected)[0]

def test_input_validation():
    with pytest.raises(ValueError):make_task('unknown',0)

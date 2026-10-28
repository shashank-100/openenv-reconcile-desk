"""Original task generator using attributed, pinned Pool Desk government data."""
import csv
import io
import random
import re
from decimal import Decimal
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/'upstream'/'data'
TASKS=('source-spend','revised-payments','duplicate-exports','cancelled-payments','mixed-reconciliation')
DEPARTMENTS=('dwp','dbt','defra')
HEADER=['supplier',*DEPARTMENTS,'total']

def normalize(value):
    words=re.sub(r'[^A-Z0-9 ]',' ',value.upper()).split()
    return tuple(w for w in words if w not in {'LTD','LIMITED','PLC','UK'})

def cents(value):
    number=Decimal(value.replace('£','').replace(',','').strip())
    if not number.is_finite() or number*100!=(number*100).to_integral_value():
        raise ValueError('Not a finite money amount in whole pennies')
    return int(number*100)

def money(value):
    return format(Decimal(value)/100,'.2f')

def read_sources():
    suppliers=(DATA/'suppliers.txt').read_text().splitlines()
    index={normalize(s):s for s in suppliers}
    records=[]
    for dept in DEPARTMENTS:
        with (DATA/f'{dept}_spend_feb2026.csv').open(encoding='cp1252',newline='') as f:
            for line,raw in enumerate(csv.DictReader(f),1):
                row={k.strip():v for k,v in raw.items() if k is not None}
                name=row.get('Supplier Name',row.get('Supplier',''))
                if normalize(name) not in index: continue
                amount=row.get('Transparency Invoice Amount',row.get('Amount',''))
                records.append({'record_id':f'{dept}-{line:06}', 'supplier':name,'canonical':index[normalize(name)],'department':dept,'amount':cents(amount)})
    return suppliers,records

def totals(suppliers,records):
    result={s:{d:0 for d in DEPARTMENTS} for s in suppliers}
    for record in records: result[record['canonical']][record['department']]+=record['amount']
    return [[s,*[money(result[s][d]) for d in DEPARTMENTS],money(sum(result[s].values()))] for s in suppliers]

def csv_text(header,rows):
    buffer=io.StringIO(); writer=csv.writer(buffer,lineterminator='\n')
    writer.writerow(header);writer.writerows(rows)
    return buffer.getvalue()

def make_task(task_id,seed):
    if task_id not in TASKS: raise ValueError('Unknown task_id')
    rng=random.Random(seed)
    suppliers,source=read_sources()
    common=(
        'Compute supplier spending by department in GBP. Write supplier_spend.csv in your workspace. '
        'Header must be supplier,dwp,dbt,defra,total. Include one row per entry in suppliers.txt, in that order, '
        'with the exact listed name. Values must be plain finite decimals with exactly two fractional digits '
        '(no commas, currency symbols, NaN or Infinity). Missing department amounts are 0.00; total is the '
        'sum of the three departments. Credits are negative and reduce spending. '
        'Name matching: uppercase, replace each character outside A-Z, 0-9 and space with a space, '
        'split into words, remove LTD/LIMITED/PLC/UK, and compare the remaining words in order. '
        'Use exec to run shell/Python commands, write_file to create scripts, check for nonterminal feedback, '
        'and evaluate to finish. Maximum 32 actions. All rules and required input files are public in the workspace. '
    )
    files={'suppliers.txt':('\n'.join(suppliers)+'\n').encode()}
    if task_id=='source-spend':
        for dept in DEPARTMENTS:
            name=f'{dept}_spend_feb2026.csv';files[name]=(DATA/name).read_bytes()
        instruction=common+(
            'Inputs are the three *_spend_feb2026.csv files. Read them using cp1252 encoding. '
            'DWP uses Supplier Name and Transparency Invoice Amount; DBT and Defra use Supplier and Amount. '
            'Trim header whitespace, including the trailing space in Defra Supplier. Amounts can contain £, '
            'thousands separators and whitespace. Each input row is a separate payment; do not deduplicate these source files. '
            'This baseline reuses the GOV.UK input slice curated by vibrantlabsai/Pool Desk v5, under OGL v3.0.')
        expected=totals(suppliers,source)
    else:
        # A transparent synthetic exercise derived from real payment amounts.
        source=[dict(r) for r in source]
        rng.shuffle(source)
        selected=[]
        for s in suppliers:
            matches=[r for r in source if r['canonical']==s]
            selected.extend(matches[:rng.randint(4,8)])
        latest=[];export=[]
        for i,record in enumerate(selected):
            record=dict(record)
            # Per-episode pseudonyms prevent a fixed-output lookup of the public originals.
            record['record_id']=f'p-{rng.getrandbits(48):012x}-{i}'
            record['amount']+=rng.randint(-25000,25000)
            current={**record,'revision':1,'status':'posted'}
            export.append(dict(current))
            if task_id in ('revised-payments','mixed-reconciliation') and i%4==0:
                current={**current,'revision':2,'amount':current['amount']+rng.choice([-1,1])*rng.randint(101,50000)}
                export.append(dict(current))
            if task_id in ('cancelled-payments','mixed-reconciliation') and i%5==0:
                current={**current,'revision':current['revision']+1,'status':'cancelled'}
                export.append(dict(current))
            if task_id in ('duplicate-exports','mixed-reconciliation') and i%3==0:
                export.extend([dict(current),dict(current)])
            if current['status']=='posted': latest.append(current)
        rng.shuffle(export)
        fields=['record_id','revision','supplier','department','amount','status']
        files['payments.csv']=csv_text(fields,[[r[k] if k!='amount' else money(r[k]) for k in fields] for r in export]).encode()
        instruction=common+(
            'Input payments.csv is UTF-8. It is a SYNTHETIC ledger derived from public spending amounts; corrections, '
            'cancellations, record IDs and amount perturbations are artificial training data, not government claims. '
            'For each record_id, select its highest integer revision, regardless of row order. Identical repeats of '
            'the same record_id/revision are duplicate exports and count once. Revisions replace earlier records; '
            'they are not extra payments. Include only records whose selected status is posted. A selected cancelled '
            'record contributes zero. Never deduplicate different record_id values merely because their amounts match. '
            'Supplier matching and required output are described above.')
        expected=totals(suppliers,latest)
    files['instruction.txt']=instruction.encode()
    return instruction,files,expected

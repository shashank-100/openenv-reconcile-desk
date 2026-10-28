import csv,io,re
from decimal import Decimal
from pathlib import Path
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

files={p.name:p.read_bytes() for p in Path(".").iterdir() if p.is_file() and (p.name=="suppliers.txt" or p.name.endswith(".csv")) and p.name!="supplier_spend.csv"}
rows=independent_solution(files)
with open("supplier_spend.csv","w",newline="") as out:
 writer=csv.writer(out);writer.writerow(["supplier","dwp","dbt","defra","total"]);writer.writerows(rows)

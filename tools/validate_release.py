"""Validate recorded evidence, manuscript figures, and exported CSV tables."""
from pathlib import Path
import csv
import hashlib
import json
import os
import sys
import numpy as np
from PIL import Image
from core_runner import verify_frozen

ROOT=Path(__file__).resolve().parents[1]
REV=ROOT/'datas/revision_20260909'
SKIP={'.git','outputs','node_modules','__pycache__','.mplconfig','.venv'}
EXPECTED_FIGURES = {
    'Framework': '4291ec80db2108cf084b253ba96ea42def49550e39c86b3719a5fc66340b4f11',
    'Fig01_Workload_Mapping': '1356a2a10f9238d93b4d2530a310d70cbafa62b3b73197ea2ec2cd8d494a8a01',
    'Fig02_Main_Comparison': '519d09749c5171282861f876d5ab6e92282b1ada1e992f138135d3e574bdfdef',
    'Fig03_Advanced_Comparison_a_Replaced': 'bbdc183058cd3df6f4263c2b33fc7e49fcb16ce90019ccfa001ca328a239232a',
    'Fig04_Matched_Initialization': '15bda56914cf1c19891387408ff66ca6e7f163d13b45f13bb345b1c166978f33',
    'Fig05_Ablation_Single_Panel': '435a09374161ded877df02ac2319400c57bfcab649658c48383d4234c829321a',
    'Fig06_Controlled_Ablation': '987db6774b44f9c2a5b84c02aa8e8840bc82ed52a7de357ac7f772ef2d1209a5',
    'Fig07_Parameter_Sensitivity': '92cd17e89dd2d28dfe469a3a6e3b7a8c830614ea25716d45ac2f71f418b4231e',
    'Fig08_Prespecified_Temperature': 'dfb10d2ec5421b7300242bd1feab8fc87a7b8afcf2e33373bd3722b424e6bae4',
    'Fig09_Resource_Scarcity': '433c007a53ae21cf94979efb96f2a979706165536da3e579063a5d019c1a7eda',
    'Fig10_Scenario_Transfer': '1b368b1d446e7d865cf71e17deeb1b4ee417345876e7e5ed67db1568e8fd6e17',
    'Fig11_Prespecified_Configurations': '7e3980ce8d245be7f64e1796b8ba8d342a20a03653f8cbc38105a35698eecd7b',
    'Fig12_Scalability': '5d6b098068d76a50e29f20820ec89e1adcbafc7ea063b87ef96ef8a8644af87e',
    'Fig13_Dynamic_Warm_Start': '0ba8c82fe4b6114627b18033a5f3c2348cbd822ce76dca0c37dd5687347dc14a',
}

def files():
    for folder,dirs,names in os.walk(ROOT):
        dirs[:]=sorted(d for d in dirs if d not in SKIP)
        for name in sorted(names):
            p=Path(folder)/name
            if name.endswith(('.pyc','.inspect.ndjson')): continue
            yield p

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    verify_frozen()
    assert sha(REV/'revision_raw.csv')=='d9e1c943ffac3bb67ac27a105a00be981ca7c713e8bacad1435267e20b0e0f63'
    with (REV/'revision_raw.csv').open(encoding='utf-8-sig',newline='') as stream: rows=list(csv.DictReader(stream))
    records=list((REV/'run_records').glob('*.json'))
    assert len(rows)==len(records)==2040
    assert len(list((REV/'instances').rglob('*.npz')))==180
    keys=set()
    for row in rows:
        key=f"{row['suite']}_{row['scenario']}_{int(row['run']):02d}_{row['budget']}_{row['initialization']}_{row['algorithm']}"
        assert key not in keys; keys.add(key)
        d=json.loads((REV/'run_records'/f'{key}.json').read_text())
        assert abs(float(row['objective'])-d['metrics']['objective'])<1e-12
        assert int(row['evaluations'])==(1 if row['algorithm']=='Offload-then-Allocate' else int(row['budget']))
        assert np.all(np.diff(d['trace_objective'])<=1e-12)
        assert int(row['feasible'])==1
    png_names={p.stem for p in (ROOT/'images/png').glob('*.png')}
    pdf_names={p.stem for p in (ROOT/'images/pdf').glob('*.pdf')}
    assert png_names==pdf_names==set(EXPECTED_FIGURES)
    figures=[]
    for name,expected_hash in EXPECTED_FIGURES.items():
        p=ROOT/'images/png'/f'{name}.png'
        assert sha(ROOT/'images/pdf'/f'{name}.pdf')==expected_hash
        with Image.open(p) as im:
            dpi=im.info.get('dpi',(0,0))
            assert min(dpi)>=(149.0 if name=='Framework' else 599.9)
            figures.append({'name':p.name,'pixels':list(im.size),'dpi':list(dpi)})
    table_index=json.loads((ROOT/'datas/tables/table_index.json').read_text(encoding='utf-8'))
    assert [item['table'] for item in table_index]==list(range(5,16))
    assert len(list((ROOT/'datas/tables').glob('Table*.csv')))==11
    assert len(list((ROOT/'experiments').glob('*.py')))==4
    inventory=list(files())
    for p in inventory:
        assert p.stat().st_size<100*1024*1024, f'Too large for normal GitHub upload: {p}'
    report={'frozen_inputs_verified':True,'historical_csv_verified':24,'revision_records':2040,'fresh_instances':180,
            'core_entry_points':4,'manuscript_figure_pairs':len(figures),'figure_source_hashes_verified':len(figures),
            'manuscript_data_tables':len(table_index),'release_file_count':len(inventory),
            'release_bytes':sum(p.stat().st_size for p in inventory)}
    out=ROOT/'outputs/release_validation.json'; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='figures'},indent=2))

if __name__=='__main__': main()

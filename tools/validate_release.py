"""Validate publication data, figures, white/black workbooks and release hashes."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from core_runner import verify_frozen

ROOT=Path(__file__).resolve().parents[1]
REV=ROOT/'datas/revision_20260909'
SKIP={'.git','outputs','node_modules','__pycache__','.mplconfig','.venv'}
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def files():
    for folder,dirs,names in os.walk(ROOT):
        dirs[:]=sorted(d for d in dirs if d not in SKIP)
        for name in sorted(names):
            p=Path(folder)/name
            if name.endswith(('.pyc','.inspect.ndjson')) or p==ROOT/'datas/release_manifest.json': continue
            yield p

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def check_workbook(path):
    with zipfile.ZipFile(path) as z:
        assert not any('externalLink' in n or 'vbaProject' in n for n in z.namelist())
        style=ET.fromstring(z.read('xl/styles.xml'))
        fonts=style.find('s:fonts',NS); fills=style.find('s:fills',NS); xfs=style.find('s:cellXfs',NS)
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            shared=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        colored=0; cells=0; sheets=0; errors=[]
        for name in z.namelist():
            if not name.startswith('xl/worksheets/sheet') or not name.endswith('.xml'): continue
            sheets+=1
            sheet=ET.fromstring(z.read(name))
            for cell in sheet.findall('.//s:c',NS):
                xf=xfs[int(cell.get('s','0'))]
                font=fonts[int(xf.get('fontId','0'))]
                fill=fills[int(xf.get('fillId','0'))]
                color=font.find('s:color',NS)
                pattern=fill.find('s:patternFill',NS)
                fg=None if pattern is None else pattern.find('s:fgColor',NS)
                black=color is not None and color.get('rgb','').upper()[-6:]=='000000'
                white=fg is not None and fg.get('rgb','').upper()[-6:]=='FFFFFF'
                assert black and white, f'Non-white/black cell: {path.name}/{name}/{cell.get("r")}'
                if cell.get('t')=='e': errors.append(cell.get('r'))
                if cell.find('s:v',NS) is not None or cell.find('s:is',NS) is not None: cells+=1
        assert not errors, f'Excel errors: {errors}'
        return {'file':path.name,'sheets':sheets,'populated_cells':cells,'white_black_all_styled_cells':True,'excel_errors':len(errors)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest',action='store_true')
    args=parser.parse_args()
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
    figures=[]
    for p in sorted((ROOT/'images/png').glob('*.png')):
        with Image.open(p) as im:
            dpi=im.info.get('dpi',(0,0)); assert min(dpi)>=599.9
            figures.append({'name':p.name,'pixels':list(im.size),'dpi':list(dpi)})
        assert (ROOT/'images/pdf'/p.with_suffix('.pdf').name).exists()
    assert len(figures)==10 and len(list((ROOT/'images/pdf').glob('*.pdf')))==10
    workbooks=[check_workbook(p) for p in sorted((ROOT/'datas/excel').glob('*.xlsx'))]
    assert len(workbooks)==2 and sorted(x['sheets'] for x in workbooks)==[5,10]
    assert len(list((ROOT/'experiments').glob('*.py')))==4
    assert len(list((ROOT/'datas/tables').glob('Table*.csv')))==10
    inventory=[]
    for p in files():
        assert p.stat().st_size<100*1024*1024, f'Too large for normal GitHub upload: {p}'
        inventory.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    manifest=ROOT/'datas/release_manifest.json'
    if args.write_manifest:
        manifest.write_text(json.dumps({'release':'2026-09-09','files':inventory},indent=2),encoding='utf-8')
    elif manifest.exists():
        saved=json.loads(manifest.read_text())['files']
        assert saved==inventory, 'Release manifest differs; investigate before refreshing it'
    report={'frozen_inputs_verified':True,'historical_csv_verified':24,'revision_records':2040,'fresh_instances':180,
            'core_entry_points':4,'figures':figures,'workbooks':workbooks,'release_file_count':len(inventory),'release_bytes':sum(x['bytes'] for x in inventory)}
    out=ROOT/'outputs/release_validation.json'; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='figures'},indent=2))

if __name__=='__main__': main()

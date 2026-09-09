"""Regenerate English scientific figures in outputs/, without altering release images."""
from pathlib import Path
import contextlib
import importlib.util
import os
import runpy
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]

def main():
    dest=ROOT/'outputs/regenerated_figures'
    dest.mkdir(parents=True,exist_ok=True)
    os.environ['MPLCONFIGDIR']=str(dest/'mplconfig')
    os.environ['RFOTO_FIGURE_OUTPUT_ROOT']=str(dest/'historical')
    os.environ['RFOTO_FIGURE_DPI']='600'
    with (dest/'generation_log.txt').open('w',encoding='utf-8') as stream,contextlib.redirect_stdout(stream):
        runpy.run_path(str(ROOT/'tools/historical_figures.py'),run_name='__main__')
        spec=importlib.util.spec_from_file_location('revision_plots',ROOT/'experiments/revision_20260909/plot_revision.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        module.FIG=dest/'revision'
        for ext in ['png','pdf']: (module.FIG/ext).mkdir(parents=True,exist_ok=True)
        data=module.pd.read_csv(module.DATA/'revision_raw.csv')
        module.controlled_convergence(); module.component_effects()
        module.frozen_temperature(data); module.frozen_comparison(data)
    hist={'Fig1_Main_Comparison':'Fig02_Main_Comparison','Fig2_Advanced_Comparison':'Fig03_Advanced_Comparison',
          'Fig4_Ablation':'Fig05_Ablation','Fig5_Sensitivity':'Fig07_Sensitivity','Fig6_Scenario_Transfer':'Fig09_Scenario_Transfer'}
    revision={'Rev_Fig04_Matched_Initialization':'Fig04_Matched_Initialization','Rev_Fig06_Controlled_Ablation':'Fig06_Controlled_Ablation',
              'Rev_Fig08_Frozen_Temperature':'Fig08_Frozen_Temperature','Rev_Fig10_Frozen_Test':'Fig10_Frozen_Test'}
    for ext in ['png','pdf']:
        (dest/ext).mkdir(parents=True,exist_ok=True)
        for old,new in hist.items(): shutil.copy2(dest/'historical/figures'/f'{old}.{ext}',dest/ext/f'{new}.{ext}')
        for old,new in revision.items(): shutil.copy2(dest/'revision'/ext/f'{old}.{ext}',dest/ext/f'{new}.{ext}')
    from workload_figure import draw
    draw(dest)
    print(f'Regenerated ten PNG/PDF pairs at {dest}; archival images unchanged.')
if __name__=='__main__':
    main()

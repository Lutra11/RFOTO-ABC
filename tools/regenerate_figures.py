"""Regenerate English scientific figures in outputs/, without altering release images."""
from pathlib import Path
import contextlib
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
    hist={'Fig1_Main_Comparison':'Fig02_Main_Comparison_Diagnostic',
          'Fig2_Advanced_Comparison':'Fig03_Advanced_Comparison_Diagnostic',
          'Fig4_Ablation':'Fig05_Ablation_Diagnostic',
          'Fig5_Sensitivity':'Fig07_Parameter_Sensitivity_Diagnostic',
          'Fig6_Scenario_Transfer':'Fig10_Scenario_Transfer_Diagnostic'}
    for ext in ['png','pdf']:
        (dest/ext).mkdir(parents=True,exist_ok=True)
        for old,new in hist.items(): shutil.copy2(dest/'historical/figures'/f'{old}.{ext}',dest/ext/f'{new}.{ext}')
    from workload_figure import draw
    draw(dest)
    print(f'Regenerated six diagnostic PNG/PDF pairs at {dest}; author-approved manuscript images unchanged.')
if __name__=='__main__':
    main()

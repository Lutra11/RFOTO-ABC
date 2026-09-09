"""Rebuild prespecified statistics in outputs/, preserving recorded analysis."""
from pathlib import Path
import contextlib
import importlib.util
ROOT = Path(__file__).resolve().parents[1]
def main():
    destination = ROOT / 'outputs/reanalysis'
    destination.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('revision_analysis', ROOT / 'experiments/revision_20260909/analyze_revision.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ANALYSIS = destination
    with (destination / 'analysis_log.txt').open('w', encoding='utf-8') as stream, contextlib.redirect_stdout(stream):
        module.main()
    print(f'Recomputed analyses: {destination}')
if __name__ == '__main__':
    main()

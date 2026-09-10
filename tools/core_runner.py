"""Print the manuscript result tables grouped by experiment section."""
from pathlib import Path
import argparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / 'datas/RFOTO_ABC_Results.xlsx'
GROUPS = ('comparison', 'ablation', 'sensitivity', 'generalization', 'all')
GROUP_SHEETS = {
    'comparison': ['T05 Main', 'T06 Advanced', 'T07 Matched'],
    'ablation': ['T08 Ablation', 'T09 Controlled'],
    'sensitivity': ['T10 Sensitivity', 'T11 Temperature'],
    'generalization': ['T12 Transfer', 'T13 New Instances', 'T14 Scalability', 'T15 Dynamic'],
}


def selected_sheets(group):
    if group == 'all':
        return [sheet for name in GROUPS[:-1] for sheet in GROUP_SHEETS[name]]
    return GROUP_SHEETS[group]


def main(default_group=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=GROUPS, default=default_group or 'all')
    args = parser.parse_args()
    for sheet in selected_sheets(args.group):
        data = pd.read_excel(WORKBOOK, sheet_name=sheet, header=3)
        print(f'\n{sheet}\n')
        print(data.to_string(index=False))


if __name__ == '__main__':
    main()

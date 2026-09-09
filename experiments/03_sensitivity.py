"""Section 4.3.3: prespecified resource-temperature validation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from core_runner import main
if __name__ == '__main__':
    main('sensitivity')

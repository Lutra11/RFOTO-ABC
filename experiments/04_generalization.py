"""Section 4.3.4: six fresh groups under frozen configurations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from core_runner import main
if __name__ == '__main__':
    main('generalization')

"""Section 4.3.1: matched-initialization algorithm comparison."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from core_runner import main
if __name__ == '__main__':
    main('comparison')

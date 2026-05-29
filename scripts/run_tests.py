import sys
import os
from pathlib import Path

# Ensure project root is on sys.path when tests import 'app'
ROOT = str(Path(__file__).resolve().parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ['PYTHONPATH'] = ROOT

import pytest

if __name__ == '__main__':
    # Run the full test suite
    sys.exit(pytest.main(['-q']))

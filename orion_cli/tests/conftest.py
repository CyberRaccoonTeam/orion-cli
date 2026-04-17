"""Configuration pytest pour Orion CLI."""

import sys
from pathlib import Path

# S'assure que src/ est dans le path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

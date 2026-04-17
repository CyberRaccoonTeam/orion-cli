"""Point d'entrée racine Orion CLI."""
import sys
from pathlib import Path

# Add project root to sys.path so top-level packages are importable
_ROOT = Path(__file__).parent
_PROJECT_ROOT = _ROOT.parent
# Do not add the entire project root to sys.path — only add this package's
# `src` directory above so installed packages are preferred.

# Ajoute src/ au path si pas installé via pip
_src_path = str(Path(__file__).parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)


from orion.main import entry_point

if __name__ == "__main__":
    entry_point()

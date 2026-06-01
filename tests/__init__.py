import sys
from pathlib import Path


# Добавляем корень проекта в sys.path, чтобы тесты видели src как пакет
sys.path.append(str(Path(__file__).parent.parent / "src"))

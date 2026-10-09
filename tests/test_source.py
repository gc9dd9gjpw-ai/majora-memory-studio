"""Distribution smoke checks; no game-state or console claims."""
from pathlib import Path
import importlib.util
import json
SOURCE = Path(__file__).resolve().parents[1] / 'src'
for path in SOURCE.glob('*.py'):
    compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec')
for path in SOURCE.glob('*.json'):
    json.loads(path.read_text(encoding='utf-8-sig'))
spec = importlib.util.spec_from_file_location('studio_smoke', SOURCE / 'Majora-Memory-Editor-v1.2.2.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert callable(module.App) and callable(module.edit)
print('PASS: source syntax, JSON and entry-point import')

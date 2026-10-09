"""Build without reference ROMs or Memories."""
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parent
if sys.platform != 'win32':
    raise SystemExit('Build the Windows executable on Windows.')
subprocess.run([
    sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
    '--onefile', '--windowed', '--name', 'Majora-Memory-Editor-v1.2.2',
    '--distpath', str(ROOT / 'dist'), '--workpath', str(ROOT / 'build'),
    '--specpath', str(ROOT / 'build'), '--add-data', str(ROOT / 'src') + ';.',
    '--hidden-import', 'tkinter', '--hidden-import', 'tkinter.ttk',
    '--hidden-import', 'tkinter.filedialog', '--hidden-import', 'tkinter.messagebox',
    '--hidden-import', 'tempfile', str(ROOT / 'src/Majora-Memory-Editor-v1.2.2.py')
], check=True, cwd=ROOT)

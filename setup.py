from pathlib import Path
import shutil
BASE = Path(__file__).resolve().parent
source = BASE / "CV_2026-10-15_Gloria_NZIENGI (1).pdf"
target = BASE / "static" / "uploads" / "CV_2026-10-15_Gloria_NZIENGI.pdf"
target.parent.mkdir(parents=True, exist_ok=True)
if source.exists() and not target.exists():
    shutil.copy2(source, target)
print("Setup terminé. Lancez : python app.py")

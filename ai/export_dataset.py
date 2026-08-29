"""Export phone-labelled FreshFusion images into ImageFolder train/val directories."""
from pathlib import Path
import random, shutil, sqlite3

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'freshfusion.db'
UPLOADS=ROOT/'uploads'
OUT=ROOT/'datasets'/'freshness'
VALID={'fresh','ripe','overripe','spoiled'}
random.seed(42)
if not DB.exists(): raise SystemExit(f"Database not found: {DB}")
con=sqlite3.connect(DB); rows=con.execute("SELECT filename, ground_truth FROM fruit_images WHERE ground_truth IS NOT NULL").fetchall(); con.close()
rows=[r for r in rows if r[1] in VALID and (UPLOADS/r[0]).exists()]
random.shuffle(rows)
for label in VALID:
    items=[r for r in rows if r[1]==label]; cut=max(1,int(len(items)*.8)) if len(items)>1 else len(items)
    for idx,(name,_) in enumerate(items):
        split='train' if idx<cut else 'val'; dest=OUT/split/label; dest.mkdir(parents=True,exist_ok=True); shutil.copy2(UPLOADS/name,dest/name)
print(f"Exported {len(rows)} labelled images to {OUT}")

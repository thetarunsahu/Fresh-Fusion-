from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'freshfusion.db'}")
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]

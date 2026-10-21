"""Project-wide settings. Edit TEAM before submitting."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "MatEIS"
APP_TAGLINE = "Materials Engineering Interactive Suite"
COURSE = "CSC-214 MATLAB and Python – CEP / OEL"
INSTRUCTOR = "Dr.-Ing. Waseem Amin"
DEPARTMENT = "B.Sc. Metallurgy & Materials Engineering, University of the Punjab, Lahore"

# Fill in before submission: (name, registration number, session)
TEAM: list[tuple[str, str, str]] = [
    ("Team member 1", "—", "Session 2023"),
    ("Team member 2", "—", "Session 2024"),
    ("Team member 3", "—", "Session 2026"),
]

DATA_DIR = Path(os.environ.get("MATEIS_DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("MATEIS_DB_PATH", DATA_DIR / "mateis.db"))
MATERIALS_SEED = ROOT / "data" / "materials_seed.json"
EMF_SEED = ROOT / "data" / "emf_series.json"
STORAGE_SECRET = os.environ.get("MATEIS_STORAGE_SECRET", "mateis-local-secret-change-me")

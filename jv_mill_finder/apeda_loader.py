import logging
from pathlib import Path

import pandas as pd

try:
    from .config import APEDA_CLEANED_FILE, TARGET_CITIES
    from .utils import extract_city, extract_pincode, normalize_company_name
except ImportError:  # pragma: no cover
    from config import APEDA_CLEANED_FILE, TARGET_CITIES
    from utils import extract_city, extract_pincode, normalize_company_name


EXPECTED_COLUMNS = ["S.No.", "Exporter Name", "Address", "E-Mail", "State", "Exporter Type"]


def load_and_clean_apeda(csv_files: list[str]) -> pd.DataFrame:
    known_cities = [city for cities in TARGET_CITIES.values() for city in cities] + ["Delhi"]
    frames: list[pd.DataFrame] = []

    for csv_file in csv_files:
        path = Path(csv_file)
        if not path.exists():
            raise FileNotFoundError(f"APEDA CSV file not found: {csv_file}")
        frame = pd.read_csv(path)
        for column in EXPECTED_COLUMNS:
            if column not in frame.columns:
                frame[column] = ""
        frames.append(frame[EXPECTED_COLUMNS].copy())

    master = pd.concat(frames, ignore_index=True)
    master["Exporter Name"] = master["Exporter Name"].fillna("").astype(str).str.strip()
    master["Address"] = master["Address"].fillna("").astype(str).str.strip()
    master["short_name"] = master["Exporter Name"].apply(normalize_company_name)
    master["city_extracted"] = master["Address"].apply(lambda a: extract_city(a, known_cities))
    master["pincode"] = master["Address"].apply(extract_pincode)
    master = master.drop_duplicates(subset=["short_name", "Address"], keep="first")

    Path(APEDA_CLEANED_FILE).parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(APEDA_CLEANED_FILE, index=False)
    logging.info("Saved cleaned APEDA data to %s", APEDA_CLEANED_FILE)
    return master

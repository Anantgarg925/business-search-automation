import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

APEDA_CSV_FILES = [
    str(DATA_DIR / "Basmati_Rice_Exporters_data_-_Haryana.csv"),
    str(DATA_DIR / "Basmati_Rice_Exporters_data_-_Uttar_Pradesh.csv"),
    str(DATA_DIR / "Basmati_Rice_Exporters_data_-_Delhi.csv"),
]

TARGET_CITIES = {
    "Haryana": ["Karnal", "Kaithal", "Taraori", "Gharaunda", "Panipat", "Kurukshetra", "Assandh", "Nissing"],
    "Uttar Pradesh": ["Muzaffarnagar", "Saharanpur", "Hardoi", "Meerut", "Shamli", "Pilibhit"],
}

SEARCH_QUERIES = [
    "rice mill {city}",
    "basmati rice mill {city}",
    "sortex rice {city}",
    "chawal mill {city}",
    "rice manufacturer {city}",
]

FUZZY_MATCH_THRESHOLD = 85
JV_TARGET_MIN_SCORE = 50
OUTPUT_FILE = str(OUTPUT_DIR / "JV_Mill_Targets.xlsx")
RAW_RESULTS_FILE = str(OUTPUT_DIR / "google_maps_raw.csv")
APEDA_CLEANED_FILE = str(OUTPUT_DIR / "apeda_master_cleaned.csv")
CACHE_FILE = str(OUTPUT_DIR / "maps_cache.json")
PROGRESS_FILE = str(OUTPUT_DIR / "search_progress.json")
OUTREACH_FILE = str(OUTPUT_DIR / "whatsapp_outreach.txt")
ERROR_LOG_FILE = str(OUTPUT_DIR / "error_log.txt")
API_DELAY_SECONDS = 1.5
SAVE_EVERY_N_CITIES = 10

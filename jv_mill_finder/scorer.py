import pandas as pd

from utils import clean_phone_number, parse_types


PRIME_BELT = {"karnal", "kaithal", "taraori", "gharaunda"}


def calculate_jv_score(row: pd.Series) -> int:
    score = 0

    phone = clean_phone_number(str(row.get("phone_number", "")))
    website = str(row.get("website", "")).strip()
    rating = float(row.get("rating", 0) or 0)
    reviews = int(row.get("user_ratings_total", 0) or 0)
    city = str(row.get("city", "")).strip().lower()
    categories = parse_types(row.get("types", []))
    opening_hours = bool(row.get("opening_hours", False))

    if phone:
        score += 20
    if website:
        score += 15
    if rating >= 4.0:
        score += 15
    if reviews > 10:
        score += 15
    if city in PRIME_BELT:
        score += 10
    if any(category in {"food_producer", "meal_delivery"} for category in categories):
        score += 10
    if opening_hours:
        score += 10
    if reviews < 50:
        score += 5

    return min(100, score)


def score_targets(df: pd.DataFrame) -> pd.DataFrame:
    scored = df.copy()
    scored["phone_number"] = scored["phone_number"].fillna("").apply(clean_phone_number)

    mask = scored["classification"] == "DOMESTIC ONLY - JV TARGET ✅"
    scored.loc[mask, "jv_score"] = scored[mask].apply(calculate_jv_score, axis=1)
    scored.loc[~mask, "jv_score"] = 0
    scored["jv_score"] = scored["jv_score"].astype(int)

    return scored.sort_values(["jv_score", "user_ratings_total"], ascending=[False, False]).reset_index(drop=True)

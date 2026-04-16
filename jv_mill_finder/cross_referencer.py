import logging

import pandas as pd
from rapidfuzz import fuzz

from config import FUZZY_MATCH_THRESHOLD
from utils import extract_pincode, normalize_company_name


def cross_reference(google_df: pd.DataFrame, apeda_df: pd.DataFrame) -> pd.DataFrame:
    if google_df.empty:
        return google_df

    apeda = apeda_df.copy()
    apeda["short_name"] = apeda.get("short_name", "").fillna("").apply(normalize_company_name)
    apeda["pincode"] = apeda.get("pincode", "").fillna("").astype(str)

    apeda_short_names = apeda["short_name"].tolist()
    apeda_by_short = {row["short_name"]: row for _, row in apeda.iterrows() if row["short_name"]}

    results = []
    for _, row in google_df.iterrows():
        item = row.to_dict()
        name = str(item.get("name", ""))
        short_name = normalize_company_name(name)
        pincode = extract_pincode(str(item.get("formatted_address", "")))

        match_status = "DOMESTIC ONLY - JV TARGET ✅"
        matched_apeda_name = ""
        match_score = 0
        match_method = "none"

        if short_name in apeda_by_short:
            matched_apeda_name = str(apeda_by_short[short_name].get("Exporter Name", ""))
            match_status = "ALREADY EXPORTING - SKIP"
            match_score = 100
            match_method = "exact"
        else:
            best_score = 0
            best_match = None
            for _, apeda_row in apeda.iterrows():
                apeda_short = apeda_row.get("short_name", "")
                if not apeda_short:
                    continue
                score = fuzz.token_sort_ratio(short_name, apeda_short)
                if score > best_score:
                    best_score = score
                    best_match = apeda_row

            match_score = int(best_score)
            if best_match is not None:
                matched_apeda_name = str(best_match.get("Exporter Name", ""))

                if best_score >= FUZZY_MATCH_THRESHOLD:
                    match_status = "ALREADY EXPORTING - SKIP"
                    match_method = "fuzzy"
                else:
                    apeda_pin = str(best_match.get("pincode", ""))
                    if pincode and apeda_pin and pincode == apeda_pin and best_score > 70:
                        match_status = "ALREADY EXPORTING - SKIP"
                        match_method = "pincode+name"
                    elif best_score >= 70:
                        match_status = "VERIFY MANUALLY ⚠️"
                        match_method = "partial"

        item["short_name"] = short_name
        item["pincode"] = pincode
        item["matched_apeda_name"] = matched_apeda_name
        item["match_score"] = match_score
        item["match_method"] = match_method
        item["classification"] = match_status
        results.append(item)

    output = pd.DataFrame(results)
    logging.info("Cross-reference complete: %s records", len(output))
    return output

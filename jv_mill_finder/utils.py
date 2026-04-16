import json
import re
from pathlib import Path
from typing import Any

SUFFIX_PATTERNS = [
    r"PRIVATE\s+LIMITED",
    r"PVT\.?\s*LTD\.?",
    r"LIMITED",
    r"LTD\.?",
    r"INDIA",
    r"OVERSEAS",
    r"FOODS?",
    r"AGRO",
    r"INDUSTRIES?",
]


def normalize_company_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9\s]", " ", name.upper())
    for pattern in SUFFIX_PATTERNS:
        cleaned = re.sub(rf"\b{pattern}\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def extract_pincode(address: str) -> str:
    if not isinstance(address, str):
        return ""
    match = re.search(r"\b(\d{6})\b", address)
    return match.group(1) if match else ""


def extract_city(address: str, known_cities: list[str] | None = None) -> str:
    if not isinstance(address, str):
        return ""
    upper_address = address.upper()
    regex_match = re.search(
        r"\b([A-Za-z ]+?)\s*,?\s*(HARYANA|UTTAR PRADESH|DELHI)\b",
        upper_address,
    )
    if regex_match:
        return regex_match.group(1).title().strip()

    if known_cities:
        for city in known_cities:
            if city.upper() in upper_address:
                return city

    parts = [p.strip() for p in re.split(r",|\n", address) if p.strip()]
    for part in reversed(parts):
        if re.search(r"\d", part):
            continue
        if part.upper() in {"HARYANA", "UTTAR PRADESH", "DELHI", "INDIA"}:
            continue
        candidate = re.sub(r"[^A-Za-z\s]", "", part).strip()
        if candidate:
            return candidate.title()
    return ""


def clean_phone_number(phone_number: str) -> str:
    if not isinstance(phone_number, str):
        return ""
    digits = re.sub(r"\D", "", phone_number)
    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[-10:]
    return digits


def parse_types(value: Any) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def load_json(path: str, default: Any) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return default
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def save_json(path: str, payload: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

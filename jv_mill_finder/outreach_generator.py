from pathlib import Path

import pandas as pd

try:
    from .utils import clean_phone_number, get_google_maps_url
except ImportError:  # pragma: no cover
    from utils import clean_phone_number, get_google_maps_url


HINDI_TEMPLATE = (
    '"Namaste ji, main [YOUR NAME] bol raha hoon Delhi se. '
    "Hum basmati rice UAE aur Saudi Arabia export karte hain. "
    "Aapki mill ke baare mein pata chala — kya aap 5 minute "
    "baat kar sakte hain ek mutually beneficial arrangement ke "
    "baare mein? Aapka number APEDA export list mein nahi hai "
    "isliye main samajhta hoon aap domestic supply karte hain. "
    "Main aapko current price se 3x zyada price dilwa sakta hoon "
    'same rice ke liye. Please call/WhatsApp: [YOUR NUMBER]"'
)


def generate_outreach_file(df: pd.DataFrame, output_path: str) -> None:
    top = (
        df[(df["classification"] == "DOMESTIC ONLY - JV TARGET ✅") & (df["jv_score"] >= 60)]
        .sort_values("jv_score", ascending=False)
        .reset_index(drop=True)
    )

    lines = []
    for idx, (_, row) in enumerate(top.iterrows(), start=1):
        phone = clean_phone_number(str(row.get("phone_number", "")))
        wa_link = f"https://wa.me/91{phone}" if phone else ""
        maps_url = get_google_maps_url(row)
        lines.extend(
            [
                f"--- MILL {idx}: {row.get('name', '')} ---",
                f"City: {row.get('city', '')}",
                f"Phone: {phone}",
                f"WhatsApp Link: {wa_link}",
                f"Google Maps: {maps_url}",
                f"Rating: {row.get('rating', 0)} ({int(row.get('user_ratings_total', 0) or 0)} reviews)",
                f"JV Score: {int(row.get('jv_score', 0))}/100",
                "",
                "Hindi Message:",
                HINDI_TEMPLATE,
                "",
                "----------------------------------------",
                "",
            ]
        )

    file_path = Path(output_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("\n".join(lines), encoding="utf-8")

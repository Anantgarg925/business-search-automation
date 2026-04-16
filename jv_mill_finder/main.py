import argparse
import logging
import sys
from pathlib import Path

from apeda_loader import load_and_clean_apeda
from config import (
    APEDA_CSV_FILES,
    ERROR_LOG_FILE,
    GOOGLE_MAPS_API_KEY,
    OUTPUT_FILE,
    OUTREACH_FILE,
    TARGET_CITIES,
)
from cross_referencer import cross_reference
from excel_generator import generate_excel
from maps_searcher import GoogleMapsSearcher, QuotaExceededError
from outreach_generator import generate_outreach_file
from scorer import score_targets


def setup_logging() -> None:
    Path(ERROR_LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=ERROR_LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def build_target_scope(args) -> dict[str, list[str]]:
    if args.cities:
        requested = {city.lower() for city in args.cities}
        scoped = {}
        for state, cities in TARGET_CITIES.items():
            matched = [city for city in cities if city.lower() in requested]
            if matched:
                scoped[state] = matched
        if not scoped:
            raise ValueError("No valid cities found in input. Please use cities from config TARGET_CITIES.")
        return scoped

    if args.state:
        for state, cities in TARGET_CITIES.items():
            if state.lower() == args.state.lower():
                return {state: cities}
        raise ValueError(f"Unknown state '{args.state}'. Allowed: {', '.join(TARGET_CITIES.keys())}")

    if args.all or args.resume:
        return TARGET_CITIES

    raise ValueError("Provide one of: --cities, --state, --all, or --resume")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="JV Mill Finder")
    parser.add_argument("--cities", nargs="*", help="Run for specific cities")
    parser.add_argument("--state", help="Run for all configured cities in one state")
    parser.add_argument("--all", action="store_true", help="Run all configured cities")
    parser.add_argument("--resume", action="store_true", help="Resume from last saved progress")
    return parser.parse_args()


def main() -> int:
    setup_logging()
    args = parse_args()

    try:
        target_scope = build_target_scope(args)
        print(f"Target scope: {target_scope}")

        apeda_df = load_and_clean_apeda(APEDA_CSV_FILES)
        print(f"Loaded APEDA records: {len(apeda_df)}")

        searcher = GoogleMapsSearcher(GOOGLE_MAPS_API_KEY)
        google_df = searcher.search(target_scope, resume=args.resume)
        print(f"Google mills collected: {len(google_df)}")

        if google_df.empty:
            print("No Google Maps records found. Exiting without output generation.")
            return 0

        classified_df = cross_reference(google_df, apeda_df)
        scored_df = score_targets(classified_df)

        generate_excel(scored_df, OUTPUT_FILE)
        generate_outreach_file(scored_df, OUTREACH_FILE)

        print("\n=== JV MILL FINDER SUMMARY ===")
        print(f"Total mills found: {len(scored_df)}")
        print(f"Already exporting: {(scored_df['classification'] == 'ALREADY EXPORTING - SKIP').sum()}")
        print(f"Domestic only: {(scored_df['classification'] == 'DOMESTIC ONLY - JV TARGET ✅').sum()}")
        print(f"Verify manually: {(scored_df['classification'] == 'VERIFY MANUALLY ⚠️').sum()}")
        print(f"Excel output: {OUTPUT_FILE}")
        print(f"Outreach file: {OUTREACH_FILE}")
        return 0

    except QuotaExceededError:
        print("Google Maps API quota exceeded. Progress was saved. Use --resume after quota resets.")
        return 2
    except FileNotFoundError as exc:
        logging.exception("Missing file")
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        logging.exception("Unhandled error")
        print(f"Unexpected error: {exc}. Check error_log.txt for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

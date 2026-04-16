import logging
import time
from pathlib import Path

import googlemaps
import pandas as pd
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError
from requests.exceptions import RequestException
from tqdm import tqdm

try:
    from .config import API_DELAY_SECONDS, CACHE_FILE, PROGRESS_FILE, RAW_RESULTS_FILE, SAVE_EVERY_N_CITIES, SEARCH_QUERIES
    from .utils import load_json, save_json
except ImportError:  # pragma: no cover
    from config import API_DELAY_SECONDS, CACHE_FILE, PROGRESS_FILE, RAW_RESULTS_FILE, SAVE_EVERY_N_CITIES, SEARCH_QUERIES
    from utils import load_json, save_json


class QuotaExceededError(RuntimeError):
    pass


class GoogleMapsSearcher:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is missing. Set it in your .env file.")
        self.client = googlemaps.Client(key=api_key)
        self.cache: dict[str, dict] = load_json(CACHE_FILE, {})

    def _retry_call(self, func, *args, **kwargs):
        delays = [1, 2, 4]
        last_error = None
        for idx, delay in enumerate(delays, start=1):
            try:
                return func(*args, **kwargs)
            except (ApiError, HTTPError, Timeout, TransportError, RequestException) as exc:
                last_error = exc
                message = str(exc).upper()
                if "OVER_QUERY_LIMIT" in message or "QUOTA" in message:
                    raise QuotaExceededError(str(exc)) from exc
                if idx == len(delays):
                    break
                logging.warning("API error (%s). Retrying in %ss", exc, delay)
                time.sleep(delay)
        if isinstance(last_error, RequestException):
            raise last_error
        raise RuntimeError(f"Google Maps API call failed after retries: {last_error}")

    def _map_place(self, place: dict, city: str, state: str) -> dict:
        place_id = place.get("place_id", "")
        details = self.cache.get(place_id)
        if details is None and place_id:
            details_response = self._retry_call(
                self.client.place,
                place_id,
                fields=[
                    "place_id",
                    "name",
                    "formatted_address",
                    "formatted_phone_number",
                    "website",
                    "rating",
                    "user_ratings_total",
                    "business_status",
                    "types",
                    "opening_hours",
                    "url",
                ],
            )
            details = details_response.get("result", {})
            self.cache[place_id] = details
            time.sleep(API_DELAY_SECONDS)

        details = details or {}
        return {
            "place_id": place_id,
            "name": details.get("name") or place.get("name", ""),
            "formatted_address": details.get("formatted_address") or place.get("formatted_address", ""),
            "phone_number": details.get("formatted_phone_number", ""),
            "website": details.get("website", ""),
            "rating": details.get("rating", 0),
            "user_ratings_total": details.get("user_ratings_total", 0),
            "business_status": details.get("business_status", ""),
            "types": details.get("types") or place.get("types", []),
            "opening_hours": bool((details.get("opening_hours") or {}).get("open_now") is not None),
            "maps_url": details.get("url", ""),
            "city": city,
            "state": state,
        }

    def search(self, target_cities: dict[str, list[str]], resume: bool = False) -> pd.DataFrame:
        Path(RAW_RESULTS_FILE).parent.mkdir(parents=True, exist_ok=True)
        existing = pd.DataFrame()
        progress = {"processed": []}

        if Path(RAW_RESULTS_FILE).exists():
            existing = pd.read_csv(RAW_RESULTS_FILE)
        if resume:
            progress = load_json(PROGRESS_FILE, {"processed": []})

        processed = set(progress.get("processed", []))
        rows: list[dict] = [] if existing.empty else existing.to_dict("records")

        all_cities = [(state, city) for state, cities in target_cities.items() for city in cities]
        save_counter = 0

        for state, city in tqdm(all_cities, desc="Searching cities"):
            city_key = f"{state}::{city}".lower()
            if city_key in processed:
                continue

            city_results = []
            try:
                for pattern in SEARCH_QUERIES:
                    query = pattern.format(city=city)
                    response = self._retry_call(self.client.places, query=query)
                    places = response.get("results", [])
                    for place in places:
                        city_results.append(self._map_place(place, city, state))
                    time.sleep(API_DELAY_SECONDS)
            except QuotaExceededError:
                logging.error("Google Maps quota exceeded. Saving progress and exiting.")
                self._save_progress(rows, processed)
                save_json(CACHE_FILE, self.cache)
                raise
            except Exception as exc:
                logging.exception("Error while processing city %s, %s: %s", city, state, exc)

            if not city_results:
                logging.warning("No results found for city: %s, %s", city, state)

            before = len(rows)
            rows.extend(city_results)
            deduped = {row.get("place_id", ""): row for row in rows if row.get("place_id")}
            rows = list(deduped.values())
            after = len(rows)

            processed.add(city_key)
            save_counter += 1
            print(f"Processed {city}, {state}: +{max(0, after - before)} new unique mills")

            if save_counter % SAVE_EVERY_N_CITIES == 0:
                self._save_progress(rows, processed)
                save_json(CACHE_FILE, self.cache)

        self._save_progress(rows, processed)
        save_json(CACHE_FILE, self.cache)
        return pd.DataFrame(rows)

    def _save_progress(self, rows: list[dict], processed: set[str]) -> None:
        pd.DataFrame(rows).to_csv(RAW_RESULTS_FILE, index=False)
        save_json(PROGRESS_FILE, {"processed": sorted(processed)})

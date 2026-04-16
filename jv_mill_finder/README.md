# JV Mill Finder

Automated workflow to identify domestic-only rice mills in Haryana and Uttar Pradesh by cross-referencing Google Maps results against APEDA exporter lists.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Add `.env` in this folder:

```env
GOOGLE_MAPS_API_KEY=your_key_here
```

3. Put APEDA CSV files in `data/`:
- `Basmati_Rice_Exporters_data_-_Haryana.csv`
- `Basmati_Rice_Exporters_data_-_Uttar_Pradesh.csv`
- `Basmati_Rice_Exporters_data_-_Delhi.csv`

## Run

```bash
python main.py --cities karnal kaithal taraori
python main.py --state haryana
python main.py --all
python main.py --resume
```

## Output

Generated under `output/`:
- `JV_Mill_Targets.xlsx`
- `whatsapp_outreach.txt`
- `google_maps_raw.csv`
- `apeda_master_cleaned.csv`
- `maps_cache.json`
- `search_progress.json`
- `error_log.txt`

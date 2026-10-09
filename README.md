# Car Damage AI: repair-cost estimator

A web app built around the YOLO11n model trained in `notebook/DAMAGEPREDICTION.ipynb`.

1. **Upload a car photo** (drag and drop, or choose a file).
2. **YOLO detects damage**: boxes on the photo with their confidence (e.g. *Dent, 64.61% confidence*), how much of the photo each covers, and the inspection priority.
3. **Choose a repair method** for each type of damage found, and how many panels, dents, lamps or tyres need it. A false detection can be left out.
4. **The SQLite repair-cost database** returns the UK price range for that method, with its source: publisher, page title, link and date.
5. **The repair-cost report** shows each line, the total range and midpoint, the sources and a disclaimer. Print it, save it as PDF or download it as JSON. Every report is saved and can be reopened.

```
Cars/
├── backend/                FastAPI + YOLO + SQLite
│   ├── app/
│   │   ├── main.py         API routes; also serves the built web app
│   │   ├── detector.py     loads the YOLO weights, runs predictions
│   │   ├── assessment.py   coverage, overlap, inspection priority (notebook cells 14–28)
│   │   ├── database.py     SQLite schema and queries
│   │   ├── seed_data.py    UK prices and their sources
│   │   ├── report.py       builds the repair-cost report
│   │   └── seed.py         reload or print the price table
│   ├── models/             car_damage_yolo11n_improved.pt, the trained model
│   ├── data/               repair_costs.db (SQLite) and uploaded photos, created on first start
│   ├── tests/              pytest
│   └── run.bat             one-click start on Windows
├── frontend/               React + TypeScript (Vite)
│   ├── src/
│   └── dist/               ready-built app, served by the backend
└── notebook/DAMAGEPREDICTION.ipynb
```

## Run it

You need **Python 3.10 or newer**. Node.js is only needed to change the frontend.

**1. Get the code.**

```powershell
git clone https://github.com/Mariam576/car-damage-ai.git
cd car-damage-ai
```

The trained model, `backend\models\car_damage_yolo11n_improved.pt` (5.4 MB), is included.

**2. Start the app.** Double-click `backend\run.bat`. The first run creates `backend\.venv` and installs FastAPI, ultralytics and PyTorch (about 300 MB, 5 to 15 minutes). Keep the window open while it installs and while you use the app. If the install is interrupted, run it again: it installs whatever is missing. Or, in PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

**3. Open http://localhost:8000.** The backend serves the ready-built React app from `frontend\dist`, so one server is all you need.

If the model file is missing, the app still opens and tells you where to put it. Detection stays off until the file is there.

### Working on the frontend

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173, forwards /api to the backend on :8000
npm run build    # rebuilds frontend\dist, which the backend serves
npm test
```

## API

Interactive docs: http://localhost:8000/docs

| Method | Path | What it does |
| --- | --- | --- |
| POST | `/api/analyses` | Form upload: `image` (JPEG/PNG/WebP/BMP, up to 15 MB), optional `confidence` (0.05–0.95, default 0.25). Returns detections, a summary and the repair options for each damage type found. |
| GET | `/api/analyses/{id}` | A saved analysis. |
| GET | `/api/analyses/{id}/image` | The photo as analysed: rotated upright, with EXIF data such as GPS location removed. |
| POST | `/api/reports` | `{"analysis_id": "...", "selections": [{"damage_type": "dent", "method_id": 5, "quantity": 1}]}`. Each detected damage type needs a `method_id` or `"excluded": true`. Returns the report. |
| GET | `/api/reports`, `/api/reports/{id}` | Saved reports. |
| GET | `/api/repair-methods?damage_type=dent` | Prices and sources from SQLite. |
| GET | `/api/damage-classes`, `/api/sources`, `/api/health` | Reference data; model and database status. |

Example: one dent, paintless dent removal

```json
{
  "lines": [{ "label": "Dent", "method": "Paintless dent removal", "quantity": 1,
              "min_gbp": 60, "max_gbp": 180, "midpoint_gbp": 120,
              "source": { "publisher": "Dentscout", "url": "https://dentscout.co.uk/blog/dent-repair-cost-uk",
                          "updated": "2026-08-30", "note": "Small (up to 10 mm) £60 to £80; ..." } }],
  "totals": { "min_gbp": 60, "max_gbp": 180, "midpoint_gbp": 120, "max_open": false },
  "inspection_priority": "Visual review required",
  "estimate_status": "Indicative only - repair method requires verification"
}
```

## The repair-cost database

`backend/data/repair_costs.db` is a SQLite file, created and filled from `backend/app/seed_data.py` the first time the backend starts. Open it with any SQLite tool, such as DB Browser for SQLite.

| Table | Holds |
| --- | --- |
| `damage_classes` | The six YOLO classes, and which ones are safety items (glass, lamp, tyre) |
| `repair_methods` | Method, damage type, `min_gbp`, `max_gbp`, `max_open` (an open "£1,000+" top), unit, source and the source's own wording |
| `sources` | Publisher, title, URL, published and updated dates, date read |
| `analyses`, `reports` | Every detection run and every report. A report keeps its own copy of the prices, so later price changes don't alter it. |

The repair methods match notebook cell 27. Glass, lamps and tyres have more than one option because the price depends on the car: whether the windscreen has an ADAS camera, halogen or LED lamps, budget or premium tyres.

| Damage | Repair method | UK price | Source |
| --- | --- | --- | --- |
| Scratch | Clear-coat scratch repair | £80–£150 per panel | Chipex, 13 Jul 2026 |
| Scratch | Paintwork scratch repair | £60–£300 per panel | Chipex, 13 Jul 2026 |
| Scratch | Deep scratch repair | £200–£400 per panel | Start Rescue, 3 Apr 2025 |
| Scratch | Full-panel repaint | £350–£600 per panel | Chipex, 13 Jul 2026 |
| Dent | Paintless dent removal | £60–£180 per dent | Dentscout, updated 30 Aug 2026 |
| Dent | Dent repair and repaint | £200–£450 per dent | Damage Fix, 31 Aug 2026 |
| Crack | Panel repair | £250–£500 per panel | Bumper, updated 8 Jul 2025 |
| Crack | Panel replacement | £600–£1,000+ per panel | Bumper, updated 8 Jul 2025 |
| Glass shatter | Automotive glass replacement | £150–£400 | Bumper, updated 20 Jul 2026 |
| Glass shatter | … with ADAS recalibration | £350–£700+ | Bumper, updated 20 Jul 2026 |
| Lamp broken | Lamp assembly replacement (halogen / basic LED) | £280–£805 | Start Rescue, 18 Aug 2026 |
| Lamp broken | Lamp assembly replacement (LED / matrix LED) | £775–£1,400+ | Start Rescue, 18 Aug 2026 |
| Flat tyre | Puncture repair | £20–£45 per tyre | Drive, 16 Jul 2026 |
| Flat tyre | Tyre replacement (budget / mid-range / premium) | £45–£70 / £75–£120 / £120–£250+ | Bumper, updated 27 Jul 2026 |

All pages were read on 9 October 2026. These are published guide prices (UK consumer prices normally include VAT), not quotations. The four scratch figures in notebook cell 25 had no source, so they were replaced with sourced ones.

**To change prices**, edit `backend/app/seed_data.py`, then run `python -m app.seed --reset` from `backend`. You can also edit the `repair_methods` table directly. `python -m app.seed --show` prints the table.

## If it doesn't start

| What you see | What to do |
| --- | --- |
| "The package install did not finish" | Check the internet connection and run `run.bat` again. The full pip log is in `backend\setup-log.txt`. |
| "Python was not found" | Install Python 3.12 from python.org and tick "Add python.exe to PATH". |
| "The app could not start" | The error is printed in the window and saved in `backend\startup-error.txt`. |
| The browser says the site can't be reached | The server is still loading the model. Wait a few seconds and refresh. |
| "Address already in use" | Another copy is already running on port 8000. Close the other window, or use the one that's running. |
| "The damage model isn't loaded" in the app | `backend\models\car_damage_yolo11n_improved.pt` is missing or misnamed. |

## Settings

Environment variables, all optional:

| Variable | Default |
| --- | --- |
| `MODEL_PATH` | `backend/models/car_damage_yolo11n_improved.pt` |
| `DB_PATH` | `backend/data/repair_costs.db` |
| `UPLOAD_DIR` | `backend/data/uploads` |
| `CONFIDENCE` | `0.25`, as in the notebook |
| `IMAGE_SIZE` | `640`, as in the notebook |
| `MAX_UPLOAD_MB` | `15` |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` |
| `FRONTEND_DIST` | `frontend/dist` |

## Tests

```powershell
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

The tests swap YOLO for a stand-in detector, so they run without the weights. They cover the notebook's dent example, the priority rules, uploads, phone-photo rotation, every report validation rule, and old reports keeping their prices.

## Limits

- The model was trained for 30 epochs on CarDD. Its test mAP@50 is 67%: crack is weakest (21%), glass shatter strongest (98%). It will miss damage and sometimes report damage that isn't there, which is why each damage type can be left out of the estimate.
- Severity isn't assessed, so the repair method is a human choice, as in the notebook. A low-confidence box (below 50%) is drawn dashed and flagged.
- The repair is chosen per damage type, with a quantity. Several boxes of one type can be the same scratch, so the app doesn't count boxes as repairs.
- iPhone HEIC photos must be saved as JPEG first.
- Prices are national guide ranges. A real quote depends on the car, paint, parts and the local labour rate.

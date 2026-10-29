# Wind Forecast Monitor

A small web app for a UK electricity buyer that shows how far the national wind
generation forecast could be trusted when buying power ahead, for January 2026.

- **See the forecast you would really have had.** Pick dates in January 2026 and
  a horizon H (0 to 48 hours). For every hour, the chart shows the actual wind
  output next to the latest forecast that had been published at least H hours
  earlier.
- **Measure the error.** The accuracy panel gives mean and percentile errors, the
  bias, how the error grows with horizon, the error distribution, the error by
  time of day, and two numbers a buyer can act on: the share of forecast wind
  that turned up in 9 of 10 hours, and the shortfall to cover in 9 of 10 hours.

Deployed app: https://gznadf.vercel.app

Video walkthrough: _to be added_

## Data

Only two Elexon BMRS datasets are used, both from the public Insights API (no key
needed):

| What | Endpoint | Fields used |
|---|---|---|
| Actual generation | `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream` with `fuelType=WIND` | `startTime` (half-hourly), `generation` (MW) |
| Forecast generation | `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream` | `startTime` (hourly), `publishTime`, `generation` (MW) |

Scope: target times from 2026-01-01 00:00 to 2026-01-31 23:30 UTC, plus forecasts
published from 2025-12-29 so that a 48 h horizon can be scored on 1 January.
January is on GMT, so UTC equals UK time throughout.

What the API returned (checked while building): WINDFOR was published 8 times a
day (02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UTC), each run covering
hourly targets up to 21:00 two days later, so the longest lead time was 66.5 h.
Each run also repeats hours that have already passed; those rows can never be
picked because their publish time is after the target.

## How the forecast is chosen

For target time T and horizon H, the app uses the most recent forecast for T whose
`publishTime <= T - H`. A forecast published exactly H hours before counts; one
published a second later does not. If no run was published early enough, that hour
has no forecast. Error is defined as `forecast - actual`, so a positive error means
less wind arrived than forecast and the buyer would be short.

Metrics are computed on hourly targets (the forecast's resolution) where an actual
also exists. The chart still draws the half-hourly actuals.

## Findings for January 2026

Numbers from `docs/jan2026_metrics.json`, written by
`python scripts/summarise_january.py`. Period: all hourly targets in January 2026.
Mean actual output over those hours: 11,581 MW.

| Horizon | Hours scored | MAE (MW) | RMSE (MW) | Bias (MW) | MAE / mean actual | P90 abs error (MW) | P99 abs error (MW) | Hours forecast too high | P10 of actual ÷ forecast |
|---|---|---|---|---|---|---|---|---|---|
| 0 h | 744 | 1,794 | 2,281 | +1,593 | 15.5% | 3,764 | 6,367 | 86.8% | 0.766 |
| 4 h | 744 | 1,836 | 2,332 | +1,645 | 15.9% | 3,899 | 6,411 | 87.9% | 0.770 |
| 12 h | 744 | 1,898 | 2,379 | +1,704 | 16.4% | 3,897 | 6,216 | 87.2% | 0.761 |
| 24 h | 744 | 2,050 | 2,518 | +1,854 | 17.7% | 4,129 | 6,287 | 86.8% | 0.721 |
| 36 h | 744 | 2,259 | 2,750 | +1,951 | 19.5% | 4,263 | 6,741 | 83.5% | 0.683 |
| 48 h | 589 | 2,380 | 2,938 | +1,879 | 20.6% | 4,744 | 6,771 | 84.4% | 0.656 |

At 48 h only 589 of 744 hours can be scored, because no run reaches far enough
ahead for the late-evening hours.

1. **The forecast ran high nearly all month.** The bias was positive at every
   horizon and the forecast was above the outturn in about 83 to 88% of hours. At
   24 h the bias (1,854 MW) is about 90% of the MAE (2,050 MW), so most of the error
   is a one-sided offset rather than random scatter.
2. **Error grows with horizon, in steps.** MAE rises from 1.79 GW with the freshest
   forecast to 2.05 GW a day ahead and 2.26 GW at 36 h. Runs come out every 2 to 4
   hours, so the curve climbs in small steps.
3. **A rule of thumb for day-ahead buying (H = 24 h).** In 9 of 10 hours at least
   72% of the forecast wind arrived, and the shortfall against the forecast was no
   more than about 4.1 GW. A cautious buyer could treat about 70% of the day-ahead
   wind forecast as firm, or hold about 4 GW of cover.
4. **Night hours were hardest.** At every horizon in the table the worst hour by MAE
   fell between 01:00 and 06:00 UTC and the best between 15:00 and 21:00.

Possible reasons for the high bias, **not tested here**: FUELHH reports metered
output after any reduction the system operator orders (for example when the grid
cannot carry all the power), whereas a forecast of available wind would not
subtract that; and the two datasets may not cover exactly the same wind farms.
Checking either needs data outside the challenge's scope.

## Architecture

```
Browser (React + Vite + TypeScript, Recharts)
   │  GET /api/series, /api/accuracy, /api/meta
   ▼
FastAPI (Python)
   ├─ selection.py  latest forecast published >= H hours before each target
   ├─ metrics.py    MAE, RMSE, bias, percentiles, reliability, histogram, by hour
   └─ store.py      loads the data once, keeps it in memory
         1. cached file from an earlier download
         2. live download from Elexon (then cached)
         3. bundled snapshot, only if Elexon cannot be reached
```

The whole month is small (about 1,500 actual rows and 20,000 forecast rows), so the
back-end downloads it once with two API calls (about 2 seconds) and answers every
request from memory in tens of milliseconds.

- **Local / Docker:** nginx serves the built front-end and forwards `/api` to the
  FastAPI container.
- **Vercel:** the Vite build is served as static files and `api/index.py` runs the
  same FastAPI app as a Python function; `vercel.json` rewrites `/api/*` to it.
  The cache goes to `/tmp` there.

## Files and directories

```
.
├── api/index.py                 Vercel Python function entry (imports the FastAPI app)
├── backend/
│   ├── app/
│   │   ├── config.py            January 2026 window, horizons, cache location
│   │   ├── elexon.py            FUELHH and WINDFOR download and parsing
│   │   ├── store.py             in-memory dataset, disk cache, snapshot fallback
│   │   ├── selection.py         the "latest forecast >= H hours before" rule
│   │   ├── metrics.py           error and reliability metrics
│   │   ├── analysis.py          joins data, selection and metrics per request
│   │   └── main.py              FastAPI routes under /api
│   ├── data/jan2026_snapshot.json.gz   fallback copy of the January data (106 KB)
│   ├── tests/                   pytest: selection rule, metrics, API, cache
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              page layout and data fetching
│   │   ├── api.ts, types.ts     typed API client
│   │   ├── components/          controls, charts, stat tiles, summary text
│   │   └── styles.css           light and dark themes, mobile layout
│   ├── Dockerfile, nginx.conf   production image
│   └── vite.config.ts           dev server proxies /api to :8000
├── scripts/
│   ├── build_snapshot.py        refresh the bundled snapshot from Elexon
│   └── summarise_january.py     write docs/jan2026_metrics.json
├── docs/jan2026_metrics.json    numbers quoted in this README
├── docker-compose.yml
├── vercel.json, requirements.txt, .python-version   Vercel deployment
└── README.md
```

## Running it

### With Docker (simplest)

```bash
docker compose up --build
```

Open http://localhost:8080. The API docs are at http://localhost:8080/api/docs.

### Without Docker

Needs Python 3.12+ and Node 20.19+.

```bash
# back-end
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements-dev.txt
cd backend
uvicorn app.main:app --reload --port 8000

# front-end, in a second terminal
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173 (Vite forwards `/api` to port 8000).

### Tests

```bash
cd backend
python -m pytest
```

## Deploying to Vercel

1. Push the repository to GitHub and import it in Vercel (or run `vercel` from
   the repository root).
2. Keep the project root as the repository root. `vercel.json` already sets the
   install command, build command, output directory (`frontend/dist`), the Python
   function and the `/api` rewrite. No environment variables are needed.
3. Deploy. The first API call on a cold instance downloads the month from Elexon
   (about 2 s); later calls use the in-memory copy.

Optional settings: `WFM_CACHE_DIR` (cache folder), `WFM_HTTP_TIMEOUT` (seconds,
default 20), `WFM_CORS_ORIGINS` (comma-separated, default `*`).

## API

All routes are `GET`. `start` and `end` are dates in January 2026 (inclusive,
defaults 2026-01-01 and 2026-01-31); `horizon` is hours from 0 to 48 (default 4).
Bad values return HTTP 422.

| Route | Returns |
|---|---|
| `/api/health` | `{"status": "ok"}` |
| `/api/meta` | data coverage, number of forecast runs, where the data came from |
| `/api/series?start&end&horizon` | half-hourly actuals, and the selected hourly forecasts with their publish time and lead time |
| `/api/accuracy?start&end&horizon` | `summary` (MAE, RMSE, bias, P50/P90/P99 absolute error, share of hours too high, P10 and P50 of actual ÷ forecast, P90 shortfall), `by_horizon` (0 to 48 h in 2 h steps), `by_hour_utc`, `error_histogram` (500 MW bins) |
| `/api/docs` | interactive OpenAPI docs |

## Design decisions

- **Horizon is a minimum lead time.** That matches how a buyer works: at decision
  time only forecasts already published can be used. No upper limit is applied,
  because runs are published at hh:30 and targets are on the hour, so the forecast
  in hand at H = 48 is always at least 48.5 h old; a hard 48 h cap would leave that
  setting empty.
- **Score hourly, draw half-hourly.** WINDFOR is hourly, so interpolating it to
  half hours would invent forecast values.
- **Reliability numbers for buyers.** Besides the usual error measures, the app
  reports the 10th percentile of actual ÷ forecast ("in 9 of 10 hours at least this
  share arrived") and the 90th percentile of forecast − actual ("cover this much to
  be safe in 9 of 10 hours").
- **Load once, serve from memory.** January 2026 is history and small, so there is
  no database. The snapshot keeps a deployed demo working if Elexon is down.
- **Same app everywhere.** All routes live under `/api`, so the Vite proxy, nginx
  and Vercel rewrites all serve the front-end and API from one origin.

## Limitations

- One month of data, in winter. The error numbers should not be read as typical
  for the whole year.
- No bias correction or improved forecast is offered; the app measures the
  published forecast as it was.
- The half-hours at hh:30 are not scored, because there is no forecast for them.
- The Vercel setup is written but has not yet been deployed.

## AI tools used

An AI coding assistant (Claude Code) was used while building this project: it
helped explore the Elexon API responses, write the back-end, front-end, tests,
Docker and Vercel configuration, and draft this README. The tests, the running
app and the saved metrics file were used to check the code and every number
quoted above.

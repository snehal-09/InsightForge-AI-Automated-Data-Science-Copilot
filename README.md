# InsightForge AI — Automated Data Science Copilot

Upload a dataset. Get an instant visual EDA dashboard. Download a fully runnable Jupyter notebook with every chart already embedded.

InsightForge takes the repetitive first hour of any data science project — loading data, checking missing values, plotting distributions, spotting correlations — and automates it end to end.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## ✨ Features

- **Universal upload** — CSV, Excel (`.xlsx`/`.xls`), JSON, Parquet, TSV/TXT
- **Instant EDA dashboard** — row/column stats, missing values, duplicates, memory usage
- **Automated visualizations** — correlation heatmap, distribution histograms, category breakdowns, outlier overview
- **Rule-based insights** — flags high-missing columns, duplicate rows, high-cardinality fields
- **Optional AI summary** — plug in a Gemini API key for a natural-language dataset summary (fully optional; the app works without it)
- **Real, runnable notebooks** — the downloaded `.ipynb` isn't a static export. It's genuine, executable code that regenerates every chart, plus a data-cleaning cell and suggested next steps
- **No database required** — session state is kept in memory; everything else runs locally with pandas/matplotlib/seaborn

## 🖥️ Demo

```
Upload dataset.csv → Dashboard renders in seconds → Click "Build notebook" → Download dataset_InsightForge_Report.ipynb
```

## 🏗️ Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Uvicorn |
| Data processing | pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| Notebook generation | nbformat |
| Frontend | Vanilla HTML / CSS / JS (no build step) |
| Optional AI layer | Google Gemini API |

## 🚀 Getting Started

### Prerequisites
- Python 3.10+

### Installation

```bash
git clone https://github.com/<your-username>/insightforge-ai.git
cd insightforge-ai

python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Run

```bash
uvicorn main:app --reload --port 8000
```

Open **http://127.0.0.1:8000** in your browser.

### Optional: AI narrative summary

Add your key to `.env`:

```
GEMINI_API_KEY=your_key_here
```

Leave it blank and the app skips the AI summary — the dashboard and notebook generation work identically either way.

## 📁 Project Structure

```
InsightForge/
├── main.py                        # FastAPI app + routes
├── requirements.txt
├── .env                            # optional GEMINI_API_KEY
├── app/
│   └── services/
│       ├── loader.py               # reads csv/xlsx/json/parquet
│       ├── analysis.py             # stats + chart generation
│       ├── notebook_builder.py     # builds the runnable .ipynb
│       ├── ai_narrator.py          # optional Gemini summary
│       └── session_store.py        # in-memory session cache
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
└── data/
    ├── uploads/                    # uploaded datasets (per session)
    └── notebooks/                  # generated notebooks (per session)
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a dataset, returns a `session_id` |
| `POST` | `/api/analyze/{session_id}` | Run EDA, returns stats + chart images |
| `POST` | `/api/build-notebook/{session_id}` | Generate the `.ipynb` |
| `GET` | `/api/download-notebook/{session_id}` | Download the generated notebook |
| `GET` | `/api/health` | Health check |


## 📄 License

MIT — see [LICENSE](LICENSE) for details.

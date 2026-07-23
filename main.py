"""
InsightForge AI Copilot
-----------------------
Upload a dataset -> get an instant visual EDA dashboard -> generate and
download a full, runnable Jupyter notebook with embedded charts.
"""
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.services import session_store
from app.services.ai_narrator import generate_ai_summary
from app.services.analysis import run_full_analysis
from app.services.loader import SUPPORTED_EXTENSIONS, load_dataframe
from app.services.notebook_builder import build_notebook, save_notebook

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
NOTEBOOK_DIR = BASE_DIR / "data" / "notebooks"
FRONTEND_DIR = BASE_DIR / "frontend"

for d in (UPLOAD_DIR, NOTEBOOK_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="InsightForge AI Copilot", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
async def serve_ui():
    return FileResponse(FRONTEND_DIR / "index.html")


MAX_UPLOAD_MB = 100


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    session_id = uuid.uuid4().hex
    saved_name = f"{session_id}{ext}"
    saved_path = UPLOAD_DIR / saved_name

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_mb = saved_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_UPLOAD_MB}MB limit.")

    try:
        df = load_dataframe(saved_path)
    except Exception as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}") from exc

    if df.empty or df.shape[1] == 0:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file has no readable data.")

    session_store.create_session(
        session_id,
        original_filename=file.filename,
        saved_path=str(saved_path),
        ext=ext,
    )

    return {
        "session_id": session_id,
        "filename": file.filename,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
    }


@app.post("/api/analyze/{session_id}")
async def analyze(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please upload the file again.")

    df = load_dataframe(Path(session["saved_path"]))
    analysis = run_full_analysis(df)

    ai_summary = generate_ai_summary(analysis["overview"], analysis["insights"])
    analysis["ai_summary"] = ai_summary

    session_store.update_session(session_id, analysis=analysis)

    return {
        "session_id": session_id,
        "filename": session["original_filename"],
        **analysis,
    }


@app.post("/api/build-notebook/{session_id}")
async def build_notebook_endpoint(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please upload the file again.")

    analysis = session.get("analysis")
    if analysis is None:
        df = load_dataframe(Path(session["saved_path"]))
        analysis = run_full_analysis(df)
        session_store.update_session(session_id, analysis=analysis)

    saved_path = Path(session["saved_path"])
    nb = build_notebook(
        dataset_filename=saved_path.name,
        file_ext=session["ext"],
        analysis=analysis,
        dataset_title=Path(session["original_filename"]).stem,
    )

    notebook_filename = f"{Path(session['original_filename']).stem}_InsightForge_Report.ipynb"
    out_path = NOTEBOOK_DIR / f"{session_id}.ipynb"
    save_notebook(nb, out_path)

    session_store.update_session(session_id, notebook_path=str(out_path), notebook_filename=notebook_filename)

    return {"session_id": session_id, "notebook_filename": notebook_filename, "ready": True}


@app.get("/api/download-notebook/{session_id}")
async def download_notebook(session_id: str):
    session = session_store.get_session(session_id)
    if not session or not session.get("notebook_path"):
        raise HTTPException(status_code=404, detail="Notebook not built yet.")

    path = Path(session["notebook_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Notebook file missing on server.")

    return FileResponse(
        path,
        media_type="application/x-ipynb+json",
        filename=session["notebook_filename"],
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}

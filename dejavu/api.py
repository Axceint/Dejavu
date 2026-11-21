"""HTTP API for the review app: start a scan, poll its progress, then fetch results and exports.
Run from repo root: .venv\\Scripts\\uvicorn dejavu.api:app --reload"""
import tempfile
import threading
import uuid
import zipfile
from collections import OrderedDict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response

from .engine import LANG, scan
from .report import all_pairs_csv, payload, render

DEMO = Path(__file__).parent.parent / "tests" / "problems"
MAX_MB = 200  # same as Streamlit's default upload limit
KEEP = 20  # shortcut: scans live in memory and the oldest is dropped; store them on disk if reviewers need them after a restart
STARTER = set(LANG) | {".zip"}

app = FastAPI(title="Dejavu")
jobs = OrderedDict()
lock = threading.Lock()


def _run(job, path, base, tmp):
    def tick(stage, done, total):  # stages in order: read, parse, compare, explain
        job.update(stage=stage, done=done, total=total)

    try:
        r = scan(path, base, tick)
        job["data"] = payload(r, progress=tick)
        job["csv"] = all_pairs_csv(r)
        job["state"] = "done"
    except (FileNotFoundError, ValueError, zipfile.BadZipFile) as e:
        job.update(state="error", error=f"Couldn't scan {job['name']}: {e}")
    except Exception:
        job.update(state="error", error="The scan failed unexpectedly. Try again, or check the server log.")
        raise
    finally:
        if tmp:
            tmp.cleanup()


def _start(path, name, base=None, tmp=None):
    job_id = uuid.uuid4().hex
    job = {"state": "running", "name": name, "stage": "read", "done": 0, "total": 0}
    with lock:
        jobs[job_id] = job
        while len(jobs) > KEEP:
            jobs.popitem(last=False)
    threading.Thread(target=_run, args=(job, path, base, tmp), daemon=True).start()
    return {"id": job_id}


async def _save(up, dest):
    data = await up.read(MAX_MB * 1024 * 1024 + 1)
    if len(data) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f"{up.filename} is larger than {MAX_MB} MB.")
    dest.write_bytes(data)


@app.post("/api/scans", status_code=202)
async def create(submissions: UploadFile = File(...), starter: UploadFile | None = File(None)):
    """submissions: one .zip of .py/.cpp/.java files. starter: code every student received; matches inside it are ignored."""
    starter_name = Path(starter.filename or "").name if starter else ""
    if starter_name and Path(starter_name).suffix.lower() not in STARTER:
        raise HTTPException(400, "Starter code must be a .py, .cpp, .java or .zip file.")
    tmp = tempfile.TemporaryDirectory()
    try:
        path, base = Path(tmp.name, "submissions.zip"), None
        await _save(submissions, path)
        if starter_name:
            Path(tmp.name, "base").mkdir()
            base = Path(tmp.name, "base", starter_name)  # keep the suffix: scan() picks the language from it
            await _save(starter, base)
    except BaseException:
        tmp.cleanup()
        raise
    return _start(path, submissions.filename or "upload", base, tmp)


@app.post("/api/scans/demo", status_code=202)
def demo():
    return _start(DEMO, "demo set")


def _job(job_id, done=False):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Scan not found. Scans are kept for a short time; upload again.")
    if done and job["state"] != "done":
        raise HTTPException(409, "Scan is not finished.")
    return job


@app.get("/api/scans/{job_id}")
def status(job_id: str):
    """Poll this until state is "done" or "error"."""
    job = _job(job_id)
    return {k: job[k] for k in ("state", "name", "stage", "done", "total", "error") if k in job}


@app.get("/api/scans/{job_id}/result")
def result(job_id: str):
    return _job(job_id, done=True)["data"]


@app.get("/api/scans/{job_id}/pairs.csv")
def pairs_csv(job_id: str):
    return Response(_job(job_id, done=True)["csv"], media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="dejavu-pairs.csv"'})


@app.get("/api/scans/{job_id}/report.html")
def report(job_id: str, theme: str | None = None):
    """The review screen as one file that opens without a server. render() whitelists theme."""
    return HTMLResponse(render(_job(job_id, done=True)["data"], theme),
                        headers={"Content-Disposition": 'attachment; filename="dejavu-report.html"'})

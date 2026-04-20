"""Market Pulse — FastAPI web app.

Run locally:
    uvicorn web.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.db import init_db
from web.jobs.runner import start_worker, stop_worker
from web.routes import dashboard, generate, library, settings as settings_routes, jobs


WEB_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_worker()
    yield
    await stop_worker()


app = FastAPI(title="Market Pulse", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
app.mount("/output", StaticFiles(directory=(WEB_DIR.parent / "output")), name="output")

templates = Jinja2Templates(directory=WEB_DIR / "templates")


# Expose templates to route modules via app state
app.state.templates = templates


app.include_router(dashboard.router)
app.include_router(generate.router)
app.include_router(library.router)
app.include_router(settings_routes.router)
app.include_router(jobs.router)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):  # noqa: ARG001
    import traceback
    tb = traceback.format_exc()
    html = f"""
    <!doctype html><html><head><title>Error — Market Pulse</title>
    <link rel='stylesheet' href='/static/app.css'></head>
    <body style="font-family:monospace;padding:2rem;color:#1A1714;background:#FAF7F2">
      <h1 style='color:#C03B2E'>Unhandled exception</h1>
      <pre style='white-space:pre-wrap'>{tb}</pre>
    </body></html>
    """
    return HTMLResponse(html, status_code=500)

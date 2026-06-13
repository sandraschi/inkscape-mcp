"""Full FastAPI backend for the web dashboard — health, logs, settings."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web_sota.backend.routes.logging import router as logging_router
from web_sota.backend.log_buffer import activity_log

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.activity_log = activity_log
    log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    activity_log.start_file_watch(log_dir / "server.log")
    activity_log.info("server", "Backend started")
    yield
    activity_log.info("server", "Backend stopped")

app = FastAPI(title="inkscape-mcp-backend", version="0.1.0", lifespan=lifespan,
              docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(logging_router)

@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "inkscape-mcp-backend"}


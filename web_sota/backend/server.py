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

@app.get("/api/llm/providers")
async def llm_providers():
    import httpx
    result = {}
    for name, url in [("ollama", "http://127.0.0.1:11434/api/tags"), ("lm_studio", "http://127.0.0.1:1234/v1/models")]:
        try:
            r = httpx.get(url, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if name == "ollama":
                    result[name] = [{"name": m["name"]} for m in data.get("models", [])]
                else:
                    result[name] = [{"name": m["id"]} for m in data.get("data", [])]
            else:
                result[name] = []
        except Exception:
            result[name] = []
    if not any(result.values()):
        result["ollama"] = [{"name": "llama3.2:3b"}]
    return result


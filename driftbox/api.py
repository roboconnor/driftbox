from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import DriftboxConfig, load_config
from .service import DriftboxService

CONFIG_PATH = Path("config/development.yaml")
WEB_DIR = Path("web")

initial_config = load_config(CONFIG_PATH)
service = DriftboxService(initial_config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    service.start()
    yield
    service.stop()


app = FastAPI(
    title="Driftbox",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/status")
def status():
    return service.status()


@app.get("/api/config")
def get_config():
    return service.config.model_dump(mode="json")


@app.post("/api/config")
def update_config(config: DriftboxConfig):
    errors = config.validate_for_mode()

    if errors:
        raise HTTPException(status_code=400, detail=errors)

    service.replace_config(config)
    return {"ok": True, "status": service.status()}


@app.post("/api/restart")
def restart():
    service.restart()
    return {"ok": True, "status": service.status()}


@app.post("/api/stop")
def stop():
    service.stop()
    return {"ok": True, "status": service.status()}


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


app.mount(
    "/static",
    StaticFiles(directory=WEB_DIR),
    name="static",
)
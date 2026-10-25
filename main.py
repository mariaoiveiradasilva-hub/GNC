from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from .database import Base, SessionLocal, engine
from .routers import auth, config, pagamentos, producao, usuarios


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)  # para evoluir o banco depois, use Alembic
    with SessionLocal() as db:
        config._cfg(db)
    yield


app = FastAPI(title="GMC Sport – Produção", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, usuarios, config, producao, pagamentos):
    app.include_router(r.router)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}


# Opcional: a própria API entrega o site estático (deve ser o último mount)
if settings.static_dir and Path(settings.static_dir).is_dir():
    app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="site")

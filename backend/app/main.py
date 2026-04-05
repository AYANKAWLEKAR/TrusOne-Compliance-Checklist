from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import compliance, geoip, health, ingest
from app.config import _validate_database_url_template, settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    _validate_database_url_template(settings.database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            required_relations = {
                "regulations": connection.execute(
                    text("SELECT to_regclass('public.regulations')")
                ).scalar_one(),
                "regulation_vectors": connection.execute(
                    text("SELECT to_regclass('public.regulation_vectors')")
                ).scalar_one(),
            }
    except Exception as exc:  # pragma: no cover - exercised during manual startup
        raise RuntimeError(
            "Database startup check failed. Update DATABASE_URL in backend/.env with a real "
            "Supabase or PostgreSQL connection string, then restart the backend."
        ) from exc

    missing_relations = [name for name, value in required_relations.items() if value is None]
    if missing_relations:
        raise RuntimeError(
            "Database schema is missing required retrieval tables "
            f"({', '.join(missing_relations)}). Run `supabase db push` from the repo root "
            "to apply the latest migrations, then restart the backend."
        )
    yield


app = FastAPI(title="TrusOne Compliance API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(compliance.router)
app.include_router(geoip.router)
app.include_router(ingest.router)

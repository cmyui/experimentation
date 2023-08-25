#!/usr/bin/env python3
from databases import Database
from fastapi import FastAPI

from app import exception_handling
from app import logging
from app import settings
from app.adapters import postgres
from app.api.v1.experiments import router as experiments_router

logging.configure_logging()
exception_handling.hook_exception_handlers()

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    app.state.database = Database(
        url=postgres.create_dsn(
            dialect="postgresql",
            user=settings.DB_USER,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            password=settings.DB_PASS,
            driver="asyncpg",
        )
    )
    await app.state.database.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    await app.state.database.disconnect()


app.include_router(experiments_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

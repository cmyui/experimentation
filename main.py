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


# async def main() -> int:
#     async with Database(
#         url=postgres.create_dsn(
#             dialect="postgresql",
#             user=settings.DB_USER,
#             host=settings.DB_HOST,
#             port=settings.DB_PORT,
#             database=settings.DB_NAME,
#             password=settings.DB_PASS,
#             driver="asyncpg",
#         )
#     ) as database:
#         experiment = Experiment(
#             name="improved_donation_perks_marketing_improves_total_donations",
#             type=ExperimentType.HYPOTHESIS_TESTING,
#             description="Test whether clearer marketing of donation perks improves donation rate",
#             hypothesis=Hypothesis(
#                 metrics_effects=[
#                     MetricEffect(
#                         metric=EventSegmentationMetric(
#                             name="User Doantion",
#                             type=MetricType.EVENT_TOTALS,
#                             property_filters=[],
#                             event="user_donated",
#                         ),
#                         direction=Direction.INCREASE,
#                         minimum_goal=15.0,
#                     ),
#                 ],
#             ),
#             exposure_event="donation_page_viewed",
#             variants=[
#                 Variant(
#                     name="control",
#                     allocation=75.0,
#                     description="The existing donation perks marketing",
#                 ),
#                 Variant(
#                     name="treatment",
#                     allocation=25.0,
#                     description="The improved donation perks marketing",
#                 ),
#             ],
#             variant_allocation={
#                 "control": 75.0,
#                 "treatment": 25.0,
#             },
#             user_segments=[Segment(name="all_users", filters=[])],
#         )

#     return 0


# if __name__ == "__main__":
#     exit(asyncio.run(main()))

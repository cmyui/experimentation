import logging
from uuid import UUID

import asyncpg.exceptions

from app.context import AbstractContext
from app.errors import ServiceError
from app.models.experiment_exposures import ExperimentExposure
from app.models.experiments import Experiment
from app.models.experiments import ExperimentType
from app.repositories import experiment_exposures
from app.repositories import experiments


async def create(
    ctx: AbstractContext,
    experiment_name: str,
    experiment_type: ExperimentType,
    experiment_key: str,
) -> Experiment | ServiceError:
    try:
        datum = await experiments.create(
            ctx,
            experiment_name=experiment_name,
            experiment_type=experiment_type,
            experiment_key=experiment_key,
        )
    except asyncpg.exceptions.UniqueViolationError as exc:
        return ServiceError.EXPERIMENT_KEY_ALREADY_EXISTS
    except Exception as exc:
        logging.error(
            "An unhandled error occurred while creating an experiment",
            exc_info=exc,
            extra={
                "experiment_name": experiment_name,
                "experiment_type": experiment_type,
                "experiment_key": experiment_key,
            },
        )
        return ServiceError.FAILED_TO_CREATE_EXPERIMENT

    return datum


async def track_exposure(
    ctx: AbstractContext,
    experiment_id: UUID,
    user_id: str,
    variant_name: str,
) -> ExperimentExposure | ServiceError:
    try:
        experiment_exposure = await experiment_exposures.create(
            ctx,
            experiment_id=experiment_id,
            user_id=user_id,
            variant_name=variant_name,
        )
    except Exception as exc:
        logging.error(
            "An unhandled error occurred while tracking exposure",
            exc_info=exc,
            extra={
                "experiment_id": experiment_id,
                "user_id": user_id,
                "variant_name": variant_name,
            },
        )
        return ServiceError.FAILED_TO_TRACK_EXPOSURE

    return experiment_exposure


async def fetch_many_qualified(
    ctx: AbstractContext,
    user_id: str,
    page: int,
    page_size: int,
) -> list[Experiment] | ServiceError:
    try:
        data = await experiments.fetch_many(
            ctx,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:
        logging.error(
            "An unhandled error occurred while fetching experiments",
            exc_info=exc,
            extra={
                "user_id": user_id,
                "page": page,
                "page_size": page_size,
            },
        )
        return ServiceError.FAILED_TO_FETCH_EXPERIMENTS

    # TODO: filter out experiments that the user is not qualified for
    #       based on the user segments assigned to the experiment.

    return data

import logging

import asyncpg.exceptions

from app.context import AbstractContext
from app.errors import ServiceError
from app.models.experiments import Experiment
from app.models.experiments import ExperimentType
from app.repositories import experiments


async def create(
    ctx: AbstractContext,
    experiment_name: str,
    experiment_type: ExperimentType,
    experiment_key: str,
) -> Experiment | ServiceError:
    try:
        experiment = await experiments.create(
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

    return experiment

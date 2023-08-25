import logging
from uuid import UUID

import asyncpg.exceptions

from app.context import AbstractContext
from app.errors import ServiceError
from app.models.exposures import Exposure
from app.repositories import assignments
from app.repositories import exposures


async def track_exposure(
    ctx: AbstractContext,
    experiment_id: UUID,
    user_id: str,
) -> Exposure | ServiceError:
    try:
        assignment = await assignments.fetch_one(ctx, experiment_id, user_id)
        if assignment is None:
            # (this could also be experiment doesn't exist)
            return ServiceError.ASSIGNMENTS_NOT_FOUND

        exposure = await exposures.create(
            ctx,
            experiment_id=experiment_id,
            user_id=user_id,
            variant_name=assignment.variant_name,
        )
    except asyncpg.exceptions.UniqueViolationError as exc:
        return ServiceError.EXPOSURE_ALREADY_EXISTS
    except Exception as exc:
        logging.error(
            "An unhandled error occurred while tracking exposure",
            exc_info=exc,
            extra={
                "experiment_id": experiment_id,
                "user_id": user_id,
            },
        )
        return ServiceError.EXPOSURES_TRACK_FAILED

    return exposure

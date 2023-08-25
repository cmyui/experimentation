import logging
from uuid import UUID

import asyncpg.exceptions

from app import distribution
from app._typing import UNSET
from app._typing import Unset
from app.context import AbstractContext
from app.errors import ServiceError
from app.models.experiments import ContextualExperiment
from app.models.experiments import Experiment
from app.models.experiments import ExperimentStatus
from app.models.experiments import ExperimentType
from app.models.experiments import Hypothesis
from app.models.experiments import Variant
from app.models.exposures import Exposure
from app.repositories import assignments
from app.repositories import experiments
from app.repositories import exposures


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


async def partial_update(
    ctx: AbstractContext,
    experiment_id: UUID,
    experiment_name: str | Unset = UNSET,
    experiment_key: str | Unset = UNSET,
    experiment_type: ExperimentType | Unset = UNSET,
    description: str | Unset = UNSET,
    hypothesis: Hypothesis | Unset = UNSET,
    exposure_event: str | Unset = UNSET,
    variants: list[Variant] | Unset = UNSET,
    variant_allocation: dict[str, float] | Unset = UNSET,
    bucketing_salt: str | Unset = UNSET,
    status: ExperimentStatus | Unset = UNSET,
) -> Experiment | ServiceError:
    try:
        experiment = await experiments.partial_update(
            ctx,
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            experiment_key=experiment_key,
            experiment_type=experiment_type,
            description=description,
            hypothesis=hypothesis,
            exposure_event=exposure_event,
            variants=variants,
            variant_allocation=variant_allocation,
            bucketing_salt=bucketing_salt,
            status=status,
        )
    except Exception as exc:
        logging.error(
            "An unhandled error occurred while updating an experiment",
            exc_info=exc,
            extra={
                "experiment_id": experiment_id,
                "experiment_name": experiment_name,
                "experiment_key": experiment_key,
                "experiment_type": experiment_type,
                "description": description,
                "hypothesis": hypothesis,
                "exposure_event": exposure_event,
                "variants": variants,
                "variant_allocation": variant_allocation,
                "bucketing_salt": bucketing_salt,
                "status": status,
            },
        )
        return ServiceError.FAILED_TO_UPDATE_EXPERIMENT

    if experiment is None:
        return ServiceError.EXPERIMENT_NOT_FOUND

    return experiment


async def track_exposure(
    ctx: AbstractContext,
    experiment_id: UUID,
    user_id: str,
    variant_name: str,
) -> Exposure | ServiceError:
    try:
        exposure = await exposures.create(
            ctx,
            experiment_id=experiment_id,
            user_id=user_id,
            variant_name=variant_name,
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
                "variant_name": variant_name,
            },
        )
        return ServiceError.FAILED_TO_TRACK_EXPOSURE

    return exposure


async def fetch_and_assign_eligible_experiments(
    ctx: AbstractContext,
    user_id: str,
) -> list[ContextualExperiment] | ServiceError:
    transaction = await ctx.database.transaction()
    try:
        _experiments = await experiments.fetch_experiments(
            ctx, status=ExperimentStatus.RUNNING
        )

        # TODO: filter out experiments that the user is not qualified for
        #       based on the user segments assigned to the experiment.
        user_experiments: list[ContextualExperiment] = []

        # Assign the user to a variant for each experiment.
        for experiment in _experiments:
            variant_name = distribution.get_user_variant(experiment, user_id)
            await assignments.create(
                ctx,
                experiment.experiment_id,
                user_id,
                variant_name,
            )

            user_experiments.append(
                ContextualExperiment(
                    experiment=experiment,
                    variant_name=variant_name,
                )
            )

    except Exception as exc:
        await transaction.rollback()
        logging.error(
            "An unhandled error occurred while fetching experiments",
            exc_info=exc,
            extra={"user_id": user_id},
        )
        return ServiceError.FAILED_TO_FETCH_EXPERIMENTS
    else:
        await transaction.commit()

    return user_experiments

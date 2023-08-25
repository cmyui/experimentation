import logging
from uuid import UUID

import asyncpg.exceptions

from app import distribution
from app._typing import is_set
from app._typing import UNSET
from app._typing import Unset
from app.context import AbstractContext
from app.errors import ServiceError
from app.models.experiments import Experiment
from app.models.experiments import ExperimentStatus
from app.models.experiments import ExperimentType
from app.models.experiments import Hypothesis
from app.models.experiments import UserExperimentBucketing
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
        return ServiceError.EXPERIMENTS_KEY_ALREADY_EXISTS
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
        return ServiceError.EXPERIMENTS_CREATE_FAILED

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
    experiment = await experiments.fetch_one(ctx, experiment_id)
    if experiment is None:
        return ServiceError.EXPERIMENTS_NOT_FOUND

    # variant & variant allocations must match
    if [variants, variant_allocation].count(UNSET) == 1:
        return ServiceError.EXPERIMENTS_VARIANT_MISMATCH
    if is_set(variants) and is_set(variant_allocation):
        if len(variants) != len(variant_allocation):
            return ServiceError.EXPERIMENTS_VARIANT_MISMATCH
        if set(v.name for v in variants) != set(variant_allocation):
            return ServiceError.EXPERIMENTS_VARIANT_MISMATCH
        if not sum(variant_allocation.values()) == 100.0:
            return ServiceError.EXPERIMENTS_INVALID_VARIANT_ALLOCATION
        if any(allocation < 0 for allocation in variant_allocation.values()):
            return ServiceError.EXPERIMENTS_INVALID_VARIANT_ALLOCATION

        # TODO: should we enforce len(variants) != 1?

    # if status is being updated, validate we're good to update to the new status
    if is_set(status):
        if status is ExperimentStatus.RUNNING:
            # TODO: this is not quite right
            if not (experiment.hypothesis or (is_set(hypothesis) and hypothesis)):
                return ServiceError.EXPERIMENTS_NEEDS_HYPOTHESIS

            if not (
                experiment.exposure_event or (is_set(exposure_event) and exposure_event)
            ):
                return ServiceError.EXPERIMENTS_NEEDS_EXPOSURE_EVENT

            if not (experiment.variants or (is_set(variants) and variants)):
                return ServiceError.EXPERIMENTS_NEEDS_VARIANTS

            if not (
                experiment.variant_allocation
                or (is_set(variant_allocation) and variant_allocation),
            ):
                return ServiceError.EXPERIMENTS_NEEDS_VARIANT_ALLOCATION

            if not (
                experiment.bucketing_salt or (is_set(bucketing_salt) and bucketing_salt)
            ):
                return ServiceError.EXPERIMENTS_NEEDS_BUCKETING_SALT

        elif status is ExperimentStatus.COMPLETED:
            if experiment.status is not ExperimentStatus.RUNNING:
                return ServiceError.EXPERIMENTS_INVALID_TRANSITION

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
        return ServiceError.EXPERIMENTS_UPDATE_FAILED

    if experiment is None:
        return ServiceError.EXPERIMENTS_NOT_FOUND

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
        return ServiceError.EXPOSURES_TRACK_FAILED

    return exposure


async def fetch_and_assign_eligible_experiments(
    ctx: AbstractContext,
    user_id: str,
) -> list[UserExperimentBucketing] | ServiceError:
    transaction = await ctx.database.transaction()
    try:
        _experiments = await experiments.fetch_many(
            ctx, status=ExperimentStatus.RUNNING
        )

        # TODO: filter out experiments that the user is not qualified for
        #       based on the user segments assigned to the experiment.
        user_experiments: list[UserExperimentBucketing] = []

        # Fetch existing experiment assignments
        user_assignments = {
            assign.experiment_id: assign.variant_name
            for assign in await assignments.fetch_many(ctx, user_id=user_id)
        }

        # Fetch the user's assignments to each experiment
        for experiment in _experiments:
            variant_name = user_assignments.get(experiment.experiment_id)

            if variant_name is None:
                # User has not been assigned to a variant for this experiment.
                # Assign the user to a variant & persist to the db
                variant_name = distribution.get_user_variant(experiment, user_id)

                await assignments.create(
                    ctx,
                    experiment.experiment_id,
                    user_id,
                    variant_name,
                )

            user_experiments.append(
                UserExperimentBucketing(
                    experiment_name=experiment.name,
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
        return ServiceError.EXPERIMENTS_FETCH_FAILED
    else:
        await transaction.commit()

    return user_experiments

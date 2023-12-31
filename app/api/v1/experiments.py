import logging
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from app.api.v1 import responses
from app.api.v1.responses import Success
from app.context import HTTPAPIRequestContext
from app.errors import ServiceError
from app.models import get_all_set_fields
from app.models.experiments import Experiment
from app.models.experiments import ExperimentInput
from app.models.experiments import ExperimentUpdate
from app.models.experiments import UserExperimentBucketing
from app.models.exposures import Exposure
from app.models.exposures import ExposureInput
from app.usecases import experiments
from app.usecases import exposures

router = APIRouter(tags=["Experimentation"])


def determine_status_code(error: ServiceError) -> int:
    """Determine the appropriate http status code for a given error."""
    if error is ServiceError.EXPERIMENTS_CREATE_FAILED:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif error is ServiceError.EXPERIMENTS_FETCH_FAILED:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif error is ServiceError.EXPERIMENTS_NOT_FOUND:
        return status.HTTP_404_NOT_FOUND
    elif error is ServiceError.EXPERIMENTS_UPDATE_FAILED:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif error is ServiceError.EXPERIMENTS_DELETE_FAILED:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif error is ServiceError.EXPERIMENTS_NEEDS_HYPOTHESIS:
        return status.HTTP_400_BAD_REQUEST
    elif error is ServiceError.EXPERIMENTS_NEEDS_EXPOSURE_EVENT:
        return status.HTTP_400_BAD_REQUEST
    elif error is ServiceError.EXPERIMENTS_NEEDS_VARIANTS:
        return status.HTTP_400_BAD_REQUEST
    elif error is ServiceError.EXPERIMENTS_NEEDS_VARIANT_ALLOCATION:
        return status.HTTP_400_BAD_REQUEST
    elif error is ServiceError.EXPERIMENTS_NEEDS_BUCKETING_SALT:
        return status.HTTP_400_BAD_REQUEST
    elif error is ServiceError.EXPERIMENTS_KEY_ALREADY_EXISTS:
        return status.HTTP_409_CONFLICT
    elif error is ServiceError.EXPERIMENTS_VARIANT_MISMATCH:
        return status.HTTP_400_BAD_REQUEST
    elif error is ServiceError.EXPERIMENTS_INVALID_VARIANT_ALLOCATION:
        return status.HTTP_400_BAD_REQUEST
    elif error is ServiceError.EXPERIMENTS_INVALID_TRANSITION:
        return status.HTTP_400_BAD_REQUEST
    elif error is ServiceError.EXPOSURES_TRACK_FAILED:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif error is ServiceError.EXPOSURE_ALREADY_EXISTS:
        return status.HTTP_409_CONFLICT
    else:
        logging.warning(
            "Unhandled service error code",
            extra={
                "error": error,
                "resource": "experiments",
            },
        )
        return status.HTTP_500_INTERNAL_SERVER_ERROR


# Called by internal users


@router.post("/v1/experiments")
async def create_experiment(
    args: ExperimentInput,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[Experiment]:
    data = await experiments.create(
        ctx,
        args.experiment_name,
        args.experiment_type,
        args.experiment_key,
    )
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to create resource",
            status=determine_status_code(data),
        )
    return responses.success(data.model_dump(mode="json"))


# Called by end users


@router.get("/v1/experiments")
async def fetch_many_experiments(
    page: int = 1,
    page_size: int = 50,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[list[Experiment]]:
    data = await experiments.fetch_many_experiments(ctx, page, page_size)
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to fetch resources",
            status=determine_status_code(data),
        )

    count = await experiments.fetch_total_experiments_count(ctx)
    if isinstance(count, ServiceError):
        return responses.failure(
            error=count,
            message="Failed to fetch resources",
            status=determine_status_code(count),
        )

    return responses.success(
        content=[d.model_dump(mode="json") for d in data],
        meta={"page": page, "page_size": page_size, "total": count},
    )


@router.get("/v1/experiments/{experiment_id}")
async def fetch_one_experiment(
    experiment_id: UUID,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[Experiment]:
    data = await experiments.fetch_one_experiment(ctx, experiment_id)
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to fetch resource",
            status=determine_status_code(data),
        )
    return responses.success(data.model_dump(mode="json"))


@router.get("/v1/eligible_experiments")
async def fetch_and_assign_eligible_experiments(
    user_id: str,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[list[UserExperimentBucketing]]:
    data = await experiments.fetch_and_assign_eligible_experiments(ctx, user_id)
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to fetch resources",
            status=determine_status_code(data),
        )

    return responses.success([d.model_dump(mode="json") for d in data])


@router.patch("/v1/experiments/{experiment_id}")
async def partial_update_experiment(
    experiment_id: UUID,
    args: ExperimentUpdate,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[Experiment]:
    data = await experiments.partial_update(
        ctx,
        experiment_id,
        **get_all_set_fields(args),
    )
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to update resource",
            status=determine_status_code(data),
        )
    return responses.success(data.model_dump(mode="json"))


@router.post("/v1/experiments/{experiment_id}/exposures")
async def track_exposure(
    experiment_id: UUID,
    args: ExposureInput,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[Exposure]:
    data = await exposures.track_exposure(
        ctx,
        experiment_id,
        args.user_id,
    )
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to track exposure",
            status=determine_status_code(data),
        )

    return responses.success(data.model_dump(mode="json"))

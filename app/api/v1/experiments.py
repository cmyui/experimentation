from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from app.api.v1 import responses
from app.api.v1.responses import Success
from app.context import HTTPAPIRequestContext
from app.errors import ServiceError
from app.models.experiments import ContextualExperiment
from app.models.experiments import Experiment
from app.models.experiments import ExperimentInput
from app.models.experiments import ExperimentUpdate
from app.models.exposures import Exposure
from app.usecases import experiments

router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    """Determine the appropriate http status code for a given error."""
    if error == ServiceError.FAILED_TO_CREATE_EXPERIMENT:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif error == ServiceError.EXPERIMENT_KEY_ALREADY_EXISTS:
        return status.HTTP_409_CONFLICT
    elif error == ServiceError.EXPOSURE_ALREADY_EXISTS:
        return status.HTTP_409_CONFLICT
    else:
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
async def fetch_and_assign_eligible_experiments(
    user_id: str,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[list[ContextualExperiment]]:
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
        **args.model_dump(exclude_unset=True),
    )
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to update resource",
            status=determine_status_code(data),
        )
    return responses.success(data.model_dump(mode="json"))


@router.post("/v1/experiment-exposures")
async def track_exposure(
    experiment_id: UUID,
    user_id: str,  # TODO: some sort of implicit auth like a generated cookie?
    variant_name: str,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[Exposure]:
    data = await experiments.track_exposure(ctx, experiment_id, user_id, variant_name)
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to track exposure",
            status=determine_status_code(data),
        )

    return responses.success(data.model_dump(mode="json"))

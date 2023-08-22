from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from app.api.v1 import responses
from app.api.v1.responses import Success
from app.context import HTTPAPIRequestContext
from app.errors import ServiceError
from app.models import BaseModel
from app.models.experiments import Experiment
from app.models.experiments import ExperimentType
from app.usecases import experiments

router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    """Determine the appropriate http status code for a given error."""
    if error == ServiceError.FAILED_TO_CREATE_EXPERIMENT:
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif error == ServiceError.EXPERIMENT_KEY_ALREADY_EXISTS:
        return status.HTTP_409_CONFLICT
    else:
        return status.HTTP_500_INTERNAL_SERVER_ERROR


class ExperimentInput(BaseModel):
    name: str
    type: ExperimentType
    key: str


@router.post("/v1/experiments")
async def create_experiment(
    input_data: ExperimentInput,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[Experiment]:
    data = await experiments.create(
        ctx,
        input_data.name,
        input_data.type,
        input_data.key,
    )
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to create resource",
            status=determine_status_code(data),
        )
    return responses.success(data.model_dump(mode="json"))


@router.get("/v1/experiments")
async def fetch_many_experiments(
    user_id: str,
    page: int = 1,
    page_size: int = 50,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[list[Experiment]]:
    data = await experiments.fetch_many_qualified(ctx, user_id, page, page_size)
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to fetch resources",
            status=determine_status_code(data),
        )

    return responses.success([d.model_dump(mode="json") for d in data])


@router.post("/v1/experiment-exposures")
async def track_exposure(
    experiment_id: UUID,
    user_id: str,  # TODO: should we determine this from a cookie/header?
    variant_name: str,
    ctx: HTTPAPIRequestContext = Depends(),
) -> Success[None]:
    data = await experiments.track_exposure(ctx, experiment_id, user_id, variant_name)
    if isinstance(data, ServiceError):
        return responses.failure(
            error=data,
            message="Failed to track exposure",
            status=determine_status_code(data),
        )

    return responses.success(data.model_dump(mode="json"))

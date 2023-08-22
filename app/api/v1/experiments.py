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

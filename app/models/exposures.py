from datetime import datetime
from uuid import UUID

from app.models import BaseModel


class Exposure(BaseModel):
    experiment_id: UUID
    user_id: str
    variant_name: str
    created_at: datetime


class ExposureInput(BaseModel):
    # TODO: Add some form of "authentication"
    user_id: str

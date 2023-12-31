from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.models import BaseModel


class ExperimentType(Enum):
    HYPOTHESIS_TESTING = "hypothesis_testing"
    DO_NO_HARM = "do_no_harm"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"


class Direction(Enum):
    INCREASE = "increase"
    DECREASE = "decrease"


class MetricType(Enum):
    # event segmentation
    UNIQUES = "uniques"
    EVENT_TOTALS = "event_totals"
    PROPERTY_SUM = "property_sum"
    PROPERTY_AVERAGE = "property_average"
    # TODO
    # # formula
    # FORMULA = "formula"
    # # funnels
    # CONVERSION = "conversion"


class PropertyFilter(BaseModel):
    property: str  # event or user property
    operator: str  # TODO: enum
    value: str


class MetricBase(BaseModel):
    name: str
    type: MetricType


class EventSegmentationMetric(MetricBase):
    event: str
    property_filters: list[PropertyFilter] | None = None

    # property is only used for PROPERTY_ metric types
    property: str | None = None


class MetricEffect(BaseModel):
    metric: MetricBase
    direction: Direction
    minimum_goal: float  # %


class Hypothesis(BaseModel):
    metric_effects: list[MetricEffect]


class Variant(BaseModel):
    name: str
    description: str
    payload: Any | None = None


# class Segment(BaseModel):
#     name: str
#     filters: list[PropertyFilter]


class Experiment(BaseModel):
    experiment_id: UUID
    name: str
    key: str
    type: ExperimentType
    description: str | None
    hypothesis: Hypothesis
    exposure_event: str | None
    variants: list[Variant]
    variant_allocation: dict[str, float]  # 0.0 - 1.0
    # user_segments: list[Segment]
    bucketing_salt: str
    status: ExperimentStatus
    created_at: datetime
    updated_at: datetime


class ExperimentInput(BaseModel):
    experiment_name: str
    experiment_type: ExperimentType
    experiment_key: str


class ExperimentUpdate(BaseModel):
    experiment_name: str | None = None
    experiment_key: str | None = None
    experiment_type: ExperimentType | None = None
    description: str | None = None
    hypothesis: Hypothesis | None = None
    exposure_event: str | None = None
    variants: list[Variant] | None = None
    variant_allocation: dict[str, float] | None = None
    bucketing_salt: str | None = None
    status: ExperimentStatus | None = None


class UserExperimentBucketing(BaseModel):
    experiment_id: UUID
    variant_name: str

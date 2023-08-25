import json
import secrets
from datetime import datetime
from typing import Any
from uuid import UUID
from uuid import uuid4

from databases.interfaces import Record

from app._typing import UNSET
from app._typing import Unset
from app.context import AbstractContext
from app.models.experiments import Experiment
from app.models.experiments import ExperimentStatus
from app.models.experiments import ExperimentType
from app.models.experiments import Hypothesis
from app.models.experiments import Variant

READ_PARAMS = """\
    experiment_id, name, key, type, description, hypothesis, exposure_event,
    variants, variant_allocation, bucketing_salt, status, created_at, updated_at
"""


def serialize(experiment: Experiment) -> dict[str, Any]:
    return {
        "experiment_id": str(experiment.experiment_id),
        "name": experiment.name,
        "key": experiment.key,
        "type": experiment.type.value,
        "description": experiment.description,
        "hypothesis": json.dumps(experiment.hypothesis.model_dump(mode="json")),
        "exposure_event": experiment.exposure_event,
        "variants": json.dumps(
            [v.model_dump(mode="json") for v in experiment.variants]
        ),
        "variant_allocation": json.dumps(experiment.variant_allocation),
        "bucketing_salt": experiment.bucketing_salt,
        "status": experiment.status.value,
        "created_at": experiment.created_at,
        "updated_at": experiment.updated_at,
    }


def deserialize(data: Record) -> Experiment:
    return Experiment.model_validate(
        {
            "experiment_id": data["experiment_id"],
            "name": data["name"],
            "key": data["key"],
            "type": ExperimentType(data["type"]),
            "description": data["description"],
            "hypothesis": json.loads(data["hypothesis"]),
            "exposure_event": data["exposure_event"],
            "variants": json.loads(data["variants"]),
            "variant_allocation": json.loads(data["variant_allocation"]),
            "bucketing_salt": data["bucketing_salt"],
            "status": ExperimentStatus(data["status"]),
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
        }
    )


async def create(
    ctx: AbstractContext,
    experiment_name: str,
    experiment_type: ExperimentType,
    experiment_key: str,
) -> Experiment:
    experiment = Experiment(
        experiment_id=uuid4(),
        name=experiment_name,
        key=experiment_key,
        type=experiment_type,
        description=None,
        hypothesis=Hypothesis(metric_effects=[]),
        exposure_event=None,
        variants=[],
        variant_allocation={},
        bucketing_salt=secrets.token_hex(4),
        status=ExperimentStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    rec = await ctx.database.fetch_one(
        query=f"""\
        INSERT INTO experiments (experiment_id, name, key, type, description,
                                 hypothesis, exposure_event, variants,
                                 variant_allocation, bucketing_salt,
                                 status, created_at, updated_at)
             VALUES (:experiment_id, :name, :key, :type, :description,
                     :hypothesis, :exposure_event, :variants,
                     :variant_allocation, :bucketing_salt,
                     :status, :created_at, :updated_at)
          RETURNING {READ_PARAMS}
        """,
        values=serialize(experiment),
    )
    assert rec is not None
    return Experiment.model_validate(deserialize(rec))


async def fetch_one(
    ctx: AbstractContext,
    experiment_id: UUID,
) -> Experiment | None:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM experiments
        WHERE experiment_id = :experiment_id
    """
    values = {"experiment_id": str(experiment_id)}
    rec = await ctx.database.fetch_one(query, values)
    return deserialize(rec) if rec is not None else None


async def fetch_many(
    ctx: AbstractContext,
    status: ExperimentStatus | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[Experiment]:
    query = f"""\
        SELECT {READ_PARAMS}
          FROM experiments
    """
    values = {}

    if status is not None:
        query += """\
            WHERE status = :status
            """
        values["status"] = status.value

    query += """\
        ORDER BY rec_id DESC
    """

    if page is not None and page_size is not None:
        query += """\
            LIMIT :limit
           OFFSET :offset
        """
        values["limit"] = page_size
        values["offset"] = (page - 1) * page_size

    recs = await ctx.database.fetch_all(query, values)
    return [deserialize(rec) for rec in recs]


async def fetch_total_count(
    ctx: AbstractContext,
    status: ExperimentStatus | None = None,
) -> int:
    query = """\
        SELECT COUNT(*)
          FROM experiments
    """
    values = {}

    if status is not None:
        query += """\
            WHERE status = :status
            """
        values["status"] = status.value

    rec = await ctx.database.fetch_one(query, values)
    assert rec is not None
    return rec[0]


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
) -> Experiment | None:
    fields: dict[str, Any] = {}
    if not isinstance(experiment_name, Unset):
        fields["name"] = experiment_name
    if not isinstance(experiment_key, Unset):
        fields["key"] = experiment_key
    if not isinstance(experiment_type, Unset):
        fields["type"] = experiment_type.value
    if not isinstance(description, Unset):
        fields["description"] = description
    if not isinstance(hypothesis, Unset):
        fields["hypothesis"] = json.dumps(hypothesis.model_dump(mode="json"))
    if not isinstance(exposure_event, Unset):
        fields["exposure_event"] = exposure_event
    if not isinstance(variants, Unset):
        fields["variants"] = json.dumps([v.model_dump(mode="json") for v in variants])
    if not isinstance(variant_allocation, Unset):
        fields["variant_allocation"] = json.dumps(variant_allocation)
    if not isinstance(bucketing_salt, Unset):
        fields["bucketing_salt"] = bucketing_salt
    if not isinstance(status, Unset):
        fields["status"] = status.value

    fields["updated_at"] = datetime.now()

    query = f"""\
        UPDATE experiments
           SET {', '.join(f"{k} = :{k}" for k in fields)}
         WHERE experiment_id = :experiment_id
     RETURNING {READ_PARAMS}
    """
    values = {"experiment_id": str(experiment_id), **fields}
    rec = await ctx.database.fetch_one(query, values)
    return deserialize(rec) if rec is not None else None

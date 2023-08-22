import json
import secrets
from datetime import datetime
from typing import Any
from uuid import uuid4

from databases.interfaces import Record

from app.context import AbstractContext
from app.models.experiments import Experiment
from app.models.experiments import ExperimentType
from app.models.experiments import Hypothesis

READ_PARAMS = """\
    experiment_id, name, key, type, description, hypothesis, exposure_event,
    variants, variant_allocation, bucketing_salt, created_at, updated_at
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
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    rec = await ctx.database.fetch_one(
        query=f"""\
        INSERT INTO experiments (experiment_id, name, key, type, description,
                                 hypothesis, exposure_event, variants,
                                 variant_allocation, bucketing_salt,
                                 created_at, updated_at)
             VALUES (:experiment_id, :name, :key, :type, :description,
                     :hypothesis, :exposure_event, :variants,
                     :variant_allocation, :bucketing_salt,
                     :created_at, :updated_at)
          RETURNING {READ_PARAMS}
        """,
        values=serialize(experiment),
    )
    assert rec is not None
    return Experiment.model_validate(deserialize(rec))


async def fetch_many(
    ctx: AbstractContext,
    page: int,
    page_size: int,
) -> list[Experiment]:
    recs = await ctx.database.fetch_all(
        query=f"""\
        SELECT {READ_PARAMS}
          FROM experiments
         ORDER BY rec_id DESC
         LIMIT :limit
        OFFSET :offset
        """,
        values={
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    )
    return [deserialize(rec) for rec in recs]

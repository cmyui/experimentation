from datetime import datetime
from typing import Any
from uuid import UUID

from databases.interfaces import Record

from app.context import AbstractContext
from app.models.assignments import Assignment


READ_PARAMS = """\
    experiment_id, user_id, variant_name, created_at
"""


def serialize(experiment: Assignment) -> dict[str, Any]:
    return {
        "experiment_id": str(experiment.experiment_id),
        "user_id": experiment.user_id,
        "variant_name": experiment.variant_name,
        "created_at": experiment.created_at,
    }


def deserialize(data: Record) -> Assignment:
    return Assignment.model_validate(
        {
            "experiment_id": data["experiment_id"],
            "user_id": data["user_id"],
            "variant_name": data["variant_name"],
            "created_at": data["created_at"],
        }
    )


async def create(
    ctx: AbstractContext,
    experiment_id: UUID,
    user_id: str,
    variant_name: str,
) -> Assignment:
    assignment = Assignment(
        experiment_id=experiment_id,
        user_id=user_id,
        variant_name=variant_name,
        created_at=datetime.utcnow(),
    )
    rec = await ctx.database.fetch_one(
        f"""\
        INSERT INTO assignments (experiment_id, user_id, variant_name,
                                 created_at)
             VALUES (:experiment_id, :user_id, :variant_name, :created_at)
          RETURNING {READ_PARAMS}
        """,
        values=serialize(assignment),
    )
    assert rec is not None
    return Assignment.model_validate(deserialize(rec))

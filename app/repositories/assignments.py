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


async def fetch_one(
    ctx: AbstractContext,
    experiment_id: UUID,
    user_id: str,
) -> Assignment | None:
    rec = await ctx.database.fetch_one(
        f"""\
            SELECT {READ_PARAMS}
              FROM assignments
             WHERE experiment_id = :experiment_id
               AND user_id = :user_id
        """,
        values={
            "experiment_id": str(experiment_id),
            "user_id": user_id,
        },
    )
    return Assignment.model_validate(deserialize(rec)) if rec is not None else None


async def fetch_many(
    ctx: AbstractContext,
    experiment_id: UUID | None = None,
    user_id: str | None = None,
) -> list[Assignment]:
    query = f"""\
        SELECT {READ_PARAMS}
          FROM assignments
    """
    values = {}

    if experiment_id is not None:
        query += """\
            WHERE experiment_id = :experiment_id
        """
        values["experiment_id"] = str(experiment_id)

    if user_id is not None:
        query += """\
            WHERE user_id = :user_id
        """
        values["user_id"] = user_id

    recs = await ctx.database.fetch_all(query, values)
    return [Assignment.model_validate(deserialize(rec)) for rec in recs]

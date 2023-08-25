from typing import Any

from pydantic import BaseModel as _BaseModel


class BaseModel(_BaseModel):
    class Config:
        pass


# TODO: how can we improve the typing here?
def get_all_set_fields(args: BaseModel) -> dict[str, Any]:
    return {k: v for k, v in args.__dict__.items() if k in args.model_fields_set}

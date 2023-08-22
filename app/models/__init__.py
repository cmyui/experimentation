from pydantic import BaseModel as _BaseModel


class BaseModel(_BaseModel):
    class Config:
        pass

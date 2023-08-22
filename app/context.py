from abc import ABC
from abc import abstractproperty

from databases import Database
from fastapi import Request


class AbstractContext(ABC):
    @abstractproperty
    def database(self) -> Database:
        ...


class HTTPAPIRequestContext(AbstractContext):
    def __init__(self, request: Request) -> None:
        self._request = request

    @property
    def database(self) -> Database:
        return self._request.app.state.database

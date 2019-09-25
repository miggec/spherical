import typing


class Request(typing.NamedTuple):
    path: str
    method: str
    body: str  # an empty body is represented as ''

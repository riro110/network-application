
from abc import ABC
from dataclasses import dataclass
from typing import List, Tuple

from file import File


class Payload(ABC):
    pass


@dataclass
class PongPayload(Payload):
    address: int
    number_of_file_shared: int


@dataclass
class QueryPayload(Payload):
    search_criteria: str


@dataclass
class QueryHitPayload(Payload):
    number_of_hits: int
    address: int
    result_set: List[Tuple[int, File]]
    servent_id: int


@dataclass
class PushPayload(Payload):
    servent_id: int
    address: int
    file_index: int
    filename: str

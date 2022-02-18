
from abc import ABC
from dataclasses import dataclass


class Payload(ABC):
    pass


@dataclass
class PongPayload(Payload):
    address: int
    number_of_file_shared: int


from enum import Enum
from typing import ClassVar, Optional

from payload import Payload


class PayloadDescripter(Enum):
    PING = 1
    PONG = 2
    PUSH = 3
    QUERY = 4
    QUERY_HIT = 5


class Descripter:
    descripter_number: ClassVar[int] = 0

    def __init__(self, payload_descripter: PayloadDescripter,
                 ttl: int,
                 hops: int,
                 payload: str,
                 descripter_id: Optional[int] = None):
        if descripter_id is None:
            self.descripter_id: int = Descripter.descripter_number
            Descripter.descripter_number += 1
        else:
            self.descripter_id = descripter_id

        self.payload_descripter: PayloadDescripter = payload_descripter
        self.ttl: int = ttl
        self.hops: int = hops
        self.payload: str = payload

    def __str__(self) -> str:
        return f"<Descripter {self.descripter_id} {self.payload_descripter} ttl: {self.ttl} hops: {self.hops}>"

    def __repr__(self) -> str:
        return str(self)


class DescripterFactory:
    TTL = 2

    def create_descripter(self,
                          payload_descripter: PayloadDescripter,
                          payload: Payload,
                          descripter_id: Optional[int] = None) -> Descripter:
        return Descripter(
            payload_descripter,
            self.TTL,
            0,
            payload,
            descripter_id=descripter_id
        )

    def copy_descripter(self, descripter: Descripter) -> Descripter:
        return Descripter(
            descripter.payload_descripter,
            descripter.ttl,
            descripter.hops,
            descripter.payload,
            descripter_id=descripter.descripter_id
        )

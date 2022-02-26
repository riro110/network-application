import logging
from typing import Dict, List, Set

from .descripter import Descripter, DescripterFactory, PayloadDescripter
from .file import File, FileSet
from .payload import (PongPayload, PushPayload, QueryHitPayload,
                      QueryPayload)
from .history import History

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Servent:

    def __init__(self, network: "GnutellaNetwork"):
        self.network: GnutellaNetwork = network
        self.neighbor: Set[Servent] = set()
        self.address: int = None
        self.factory = DescripterFactory()
        self.file_set = FileSet()

        self.routing_table: Set[History] = set()
        self.from_table: Set[History] = set()
        self.servent_table: Set[History] = set()

        self.query_hit_result = []

        network.add_servent(self)

    def __str__(self) -> str:
        return f"<Servent: {self.address}>"

    def __repr__(self) -> str:
        return str(self)

    def add_neighbor(self, servent: "Servent") -> None:
        self.neighbor.add(servent)

    def add_file(self, file: File) -> None:
        self.file_set.add_file(file)

    def ping(self, address: int, descripter: Descripter = None) -> None:
        if descripter is None:
            descripter = self.factory.create_descripter(
                PayloadDescripter.PING,
                None
            )
        self.send(address, descripter)

    def pong(self, address: int, descripter: Descripter) -> None:
        self.send(address, descripter)

    def query(self, address: int, descripter: Descripter = None) -> None:
        self.send(address, descripter)

    def query_hit(self, address: int, descripter: Descripter) -> None:
        self.send(address, descripter)

    def push(self, address: int, descripter: Descripter) -> None:
        self.send(address, descripter)

    def send(self, address: int, descripter: Descripter) -> None:
        logger.info(
            f"{self} send {descripter} to {self.network.get_servent(address)}")
        descripter.ttl -= 1
        descripter.hops += 1
        self.network.get_servent(address).receive(descripter, self.address)

    def receive(self, descripter: Descripter, from_address: int) -> None:
        logger.info(
            f"{self} receive {descripter} from {self.network.get_servent(from_address)}")

        if descripter.payload_descripter == PayloadDescripter.PING:
            self.receive_ping(descripter, from_address)

        if descripter.payload_descripter == PayloadDescripter.PONG:
            self.receive_pong(descripter, from_address)

        if descripter.payload_descripter == PayloadDescripter.QUERY:
            self.receive_query(descripter, from_address)

        if descripter.payload_descripter == PayloadDescripter.QUERY_HIT:
            self.receive_query_hit(descripter, from_address)

        if descripter.payload_descripter == PayloadDescripter.PUSH:
            self.receive_push(descripter, from_address)

    def receive_ping(self, descripter: Descripter, from_address: int) -> None:
        self.routing_table.add(History(descripter.payload_descripter,
                                       descripter.descripter_id,
                                       None))
        self.from_table.add(History(descripter.payload_descripter,
                                    descripter.descripter_id,
                                    from_address))

        pong_descripter = self.factory.create_descripter(
            PayloadDescripter.PONG,
            PongPayload(
                self.address,
                0
            ),
            descripter_id=descripter.descripter_id
        )
        self.pong(from_address, pong_descripter)

        if descripter.ttl == 0:
            return

        neighbor = set(self.neighbor)
        for n in neighbor:
            if n.address == from_address:
                continue
            descripter_copy = self.factory.copy_descripter(descripter)
            self.ping(n.address, descripter_copy)

    def receive_pong(self, descripter: Descripter, from_address: int) -> None:
        self.add_neighbor(self.network.get_servent(descripter.payload.address))

        pong_history = History(PayloadDescripter.PONG,
                               descripter.descripter_id,
                               descripter.payload.address)
        if pong_history in self.routing_table \
                or descripter.ttl == 0:
            return

        ping_history = [h for h in self.from_table
                        if h.id == descripter.descripter_id and
                        h.payload_descripter == PayloadDescripter.PING]
        if ping_history:
            self.pong(ping_history[0].address, descripter)
            self.routing_table.add(pong_history)
            self.from_table.add(History(
                descripter.payload_descripter,
                descripter.descripter_id,
                from_address
            ))

    def receive_query(self, descripter: Descripter, from_address: int) -> None:
        self.routing_table.add(
            History(
                descripter.payload_descripter,
                descripter.descripter_id,
                None
            )
        )
        self.from_table.add(
            History(
                descripter.payload_descripter,
                descripter.descripter_id,
                from_address
            )
        )

        criteria = descripter.payload.search_criteria
        result = [(idx, file)
                  for idx, file in self.file_set.search_file(criteria)]

        if result:
            payload = QueryHitPayload(
                len(result),
                self.address,
                result,
                self.address
            )
            query_hit_descripter = self.factory.create_descripter(
                PayloadDescripter.QUERY_HIT,
                payload,
                descripter.descripter_id
            )
            self.query_hit(
                from_address,
                query_hit_descripter
            )

        if descripter.ttl == 0:
            return

        neighbor = set(self.neighbor)
        for n in neighbor:
            if n.address == from_address:
                continue
            descripter_copy = self.factory.copy_descripter(descripter)
            self.query(n.address, descripter_copy)

    def receive_query_hit(self, descripter: Descripter, from_address: int) -> None:
        self.routing_table.add(History(
            descripter.payload_descripter,
            descripter.descripter_id,
            None
        ))
        self.from_table.add(History(
            descripter.payload_descripter,
            descripter.descripter_id,
            from_address
        ))
        self.servent_table.add(History(
            descripter.payload_descripter,
            descripter.payload.servent_id,
            from_address
        ))

        self.query_hit_result.append(descripter)

        if descripter.ttl == 0:
            return

        query_history = [h for h in self.from_table
                         if h.id == descripter.descripter_id and
                         h.payload_descripter == PayloadDescripter.QUERY]
        if query_history:
            self.query_hit(query_history[0].address, descripter)

    def receive_push(self, descripter: Descripter, from_address: int) -> None:
        if descripter.payload.servent_id == self.address:
            file = self.file_set.get_file(descripter.payload.file_index)
            self.upload(descripter.payload.address, file)
            return

        if descripter.ttl == 0:
            return

        query_hit_history = [h for h in self.servent_table
                             if h.id == descripter.payload.servent_id and
                             h.payload_descripter == PayloadDescripter.QUERY_HIT]
        if query_hit_history:
            self.push(query_hit_history[0].address, descripter)

    def upload(self, address: int, file: File) -> None:
        target = self.network.get_servent(address)
        logger.info(f"{self} upload {file} to {target}")
        target.add_file(file)


class GnutellaNetwork:
    def __init__(self):
        self.servent_list: List[Servent] = []

    def add_servent(self, servent: Servent) -> None:
        self.servent_list.append(servent)
        servent.address = len(self.servent_list) - 1

    def get_servent(self, address) -> Servent:
        return self.servent_list[address]

    def __str__(self) -> str:
        return f"<GnutellaNetwork: {self.servent_list}>"

    def __repr__(self) -> str:
        return str(self)

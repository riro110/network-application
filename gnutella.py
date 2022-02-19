import logging
from typing import List, Optional, Set

from descripter import Descripter, DescripterFactory, PayloadDescripter
from file import FileSet, File
from payload import PongPayload, QueryPayload, QueryHitPayload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Servent:

    def __init__(self, network):
        self.network: GnutellaNetwork = network
        self.neighbor: Set[Servent] = set()
        self.address: int = None
        self.factory = DescripterFactory()
        self.file_set = FileSet()

        # {descripter_id: address}
        self.routing_table = {}

        self.query_hit_result = []

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
        self.routing_table[descripter.descripter_id] = from_address

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
        if descripter.descripter_id in self.routing_table and \
                descripter.ttl != 0:
            self.pong(self.routing_table[descripter.descripter_id], descripter)

    def receive_query(self, descripter: Descripter, from_address: int) -> None:
        self.routing_table[descripter.descripter_id] = from_address

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
        self.query_hit_result.append(descripter)
        if descripter.descripter_id in self.routing_table and \
                descripter.ttl != 0:
            self.query_hit(
                self.routing_table[descripter.descripter_id], descripter)

    def receive_push(self, descripter: Descripter, from_address: int) -> None:
        pass


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


def ping_pong():
    network = GnutellaNetwork()
    servent1 = Servent(network)
    servent2 = Servent(network)
    servent3 = Servent(network)
    servent4 = Servent(network)

    servent1.add_neighbor(servent2)

    servent2.add_neighbor(servent1)
    servent2.add_neighbor(servent3)
    servent2.add_neighbor(servent4)

    servent3.add_neighbor(servent2)

    servent4.add_neighbor(servent2)

    network.add_servent(servent1)
    network.add_servent(servent2)
    network.add_servent(servent3)
    network.add_servent(servent4)
    print(network)
    print(servent1, "has neighbor:", servent1.neighbor)
    print(servent2, "has neighbor:", servent2.neighbor)
    print(servent3, "has neighbor:", servent3.neighbor)
    print(servent4, "has neighbor:", servent4.neighbor)

    servent1.ping(1)
    print(servent1, "has neighbor:", servent1.neighbor)


def query_query_hit():
    network = GnutellaNetwork()
    servent1 = Servent(network)
    servent2 = Servent(network)
    servent3 = Servent(network)
    servent4 = Servent(network)

    servent1.add_neighbor(servent2)

    servent2.add_neighbor(servent1)
    servent2.add_neighbor(servent3)
    servent2.add_neighbor(servent4)

    servent3.add_neighbor(servent2)

    servent4.add_neighbor(servent2)

    network.add_servent(servent1)
    network.add_servent(servent2)
    network.add_servent(servent3)
    network.add_servent(servent4)

    exe_file = File("test.exe")
    servent3.add_file(exe_file)

    png_file = File("test.png")
    servent4.add_file(png_file)

    factory = DescripterFactory()

    payload = QueryPayload("test")
    descripter = factory.create_descripter(
        PayloadDescripter.QUERY,
        payload
    )

    servent1.query(servent2.address, descripter)
    print("Query Result:", servent1.query_hit_result)
    for idx, result in enumerate(servent1.query_hit_result):
        print(f"{idx+1}:")
        print("\tNumber of hits:", result.payload.number_of_hits)
        print("\tAddress:", result.payload.address)
        print("\tResult set:", result.payload.result_set)
        print("\tServent id:", result.payload.servent_id)


if __name__ == "__main__":
    # ping_pong()
    query_query_hit()

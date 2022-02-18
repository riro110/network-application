from typing import ClassVar, List, Set
from descripter import PayloadDescripter, Descripter, DescripterFactory
from payload import PongPayload
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Servent:

    def __init__(self, network):
        self.network: GnutellaNetwork = network
        self.neighbor: Set[Servent] = set()
        self.address: int = None
        self.factory = DescripterFactory()

        # {descripter_id: address}
        self.routing_table = {}

    def add_neighbor(self, servent: "Servent") -> None:
        self.neighbor.add(servent)

    def ping(self, address: int, descripter: Descripter = None) -> None:
        if descripter is None:
            descripter = self.factory.create_descripter(
                PayloadDescripter.PING,
                None
            )
        self.send(address, descripter)

    def pong(self, address: int, descripter: Descripter):
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

    def __str__(self) -> str:
        return f"<Servent: {self.address}>"

    def __repr__(self) -> str:
        return str(self)


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


if __name__ == "__main__":
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
    print(servent1.neighbor)
    print(servent2.neighbor)
    print(servent3.neighbor)
    print(servent4.neighbor)

    servent1.ping(1)
    print(servent1.neighbor)

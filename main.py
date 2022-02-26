
from gnutella.descripter import DescripterFactory, PayloadDescripter
from gnutella.file import File
from gnutella.gnutella import GnutellaNetwork, Servent
from gnutella.payload import PushPayload, QueryPayload


def create_connection(servent1: Servent, servent2: Servent) -> None:
    servent1.add_neighbor(servent2)
    servent2.add_neighbor(servent1)


def ping_pong():
    # ネットワークの定義
    network = GnutellaNetwork()
    servent1 = Servent(network)
    servent2 = Servent(network)
    servent3 = Servent(network)
    servent4 = Servent(network)

    create_connection(servent1, servent2)
    create_connection(servent2, servent3)
    create_connection(servent2, servent4)

    print(network)
    print(servent1, "has neighbor:", servent1.neighbor)
    print(servent2, "has neighbor:", servent2.neighbor)
    print(servent3, "has neighbor:", servent3.neighbor)
    print(servent4, "has neighbor:", servent4.neighbor)

    # pingを送信
    servent1.ping(1)
    print(servent1, "has neighbor:", servent1.neighbor)


def ping_pong_loop():
    DescripterFactory.TTL = 3
    # ネットワークの定義
    network = GnutellaNetwork()
    servent0 = Servent(network)
    servent1 = Servent(network)
    servent2 = Servent(network)
    servent3 = Servent(network)
    servent4 = Servent(network)

    create_connection(servent0, servent1)
    create_connection(servent1, servent2)
    create_connection(servent1, servent3)
    create_connection(servent2, servent4)
    create_connection(servent3, servent4)

    print(network)
    print(servent1, "has neighbor:", servent1.neighbor)
    print(servent2, "has neighbor:", servent2.neighbor)
    print(servent3, "has neighbor:", servent3.neighbor)
    print(servent4, "has neighbor:", servent4.neighbor)

    # pingを送信
    servent0.ping(servent1.address)
    print(servent1, "has neighbor:", servent1.neighbor)


def query_query_hit():
    # ネットワークの定義
    network = GnutellaNetwork()
    servent1 = Servent(network)
    servent2 = Servent(network)
    servent3 = Servent(network)
    servent4 = Servent(network)
    servent5 = Servent(network)

    create_connection(servent1, servent2)
    create_connection(servent2, servent3)
    create_connection(servent2, servent4)
    create_connection(servent2, servent5)

    # serventにファイルを配置
    exe_file = File("test.exe")
    servent3.add_file(exe_file)

    dummy_file = File("dummy.png")
    png_file = File("test.png")
    servent4.add_file(dummy_file)
    servent4.add_file(png_file)

    txt_file = File("test.txt")
    servent5.add_file(txt_file)

    # queryを送信
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

    # pushを送信
    target_payload = servent1.query_hit_result[0].payload
    payload = PushPayload(target_payload.servent_id,
                          servent1.address,
                          target_payload.result_set[0][0],
                          target_payload.result_set[0][1].filename,
                          )
    descripter = factory.create_descripter(
        PayloadDescripter.PUSH,
        payload
    )
    print("Servent1 file set:", str(servent1.file_set))
    servent1.push(servent2.address, descripter)
    print("Servent1 file set:", str(servent1.file_set))


if __name__ == "__main__":
    # ping_pong()
    # ping_pong_loop()
    query_query_hit()

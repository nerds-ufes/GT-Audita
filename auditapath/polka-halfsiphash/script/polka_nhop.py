"""Simulates PolKA behavior"""

from math import ceil

from crc import Configuration, Calculator


def bitmask(n: int) -> int:
    """Returns a bitmask of `n` bits.
    Example: bitmask(3) = 0b111 = 7
    """
    return (1 << n) - 1


def crc_for_node(node_id: int) -> Calculator:
    cfg = Configuration(
        width=16,
        init_value=0,
        reverse_input=False,
        reverse_output=False,
        polynomial=node_id,
        final_xor_value=0,
    )
    return Calculator(cfg)


class Node:
    def __init__(self, name: str, node_id: int, ports: list = []):
        """Initializes a node with a name and node_id.
        `ports` is a list with index equal to source port number, and value equal to a weak reference to the node it is connected to (destination port not needed)."""

        assert node_id is not None, "node_id is required"
        self.name = name
        self.node_id = node_id
        self.crc = crc_for_node(self.node_id)
        self.ports = ports

    def nhop(self, route_id: int) -> int:
        """Returns the next hop (port) for a given route_id."""

        ndata = (route_id >> 16) & bitmask(160)
        dif = (route_id ^ ((ndata << 16) & bitmask(160))) & bitmask(16)

        # Max value allowed. Only used in p4 code
        # ncount = (4294967296 * 2) & bitmask(64)

        nresult = self.crc.checksum(
            ndata.to_bytes(length=ceil(160 / 8), byteorder="big")
        )
        return (nresult ^ dif) & bitmask(9)

    def __repr__(self):
        return f"Switch({self.name})"


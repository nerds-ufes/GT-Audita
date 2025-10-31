from .polka_nhop import Node 

LINEAR_NODES = [
    Node(name, node_id)
    for (name, node_id) in [
        ("None", 0),  # Just for convenience, to match the index with the node number
        ("s1", 0x002B),
        ("s2", 0x002D),
        ("s3", 0x0039),
        ("s4", 0x003F),
        ("s5", 0x0047),
        ("s6", 0x0053),
        ("s7", 0x008D),
        ("s8", 0x00BD),
        ("s9", 0x00D7),
        ("s10", 0x00F5),
    ]
]

for i, node in enumerate(LINEAR_NODES[2:-1], start=2):  # Middle nodes
    node.ports = [
        None,  # Local (?)
        None,  # Edge
        LINEAR_NODES[i - 1],  # Node n-1 (previous)
        LINEAR_NODES[i + 1],  # Node n+1 (next)
    ]

LINEAR_NODES[1].ports = [None, None, LINEAR_NODES[2], None]  # Edge node 1. Next is on port 2
LINEAR_NODES[-1].ports = [None, None, LINEAR_NODES[-2], None]  # Edge node 10. Previous is on port 1

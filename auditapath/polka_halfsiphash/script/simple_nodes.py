from .polka_nhop import Node

SIMPLE_NODES = [
    Node(name, node_id)
    for (name, node_id) in [
        ("None", 0),  # Just for convenience, to match the index with the node number
        ("s1", 0x002B),
        ("s2", 0x002D),
        ("s3", 0x0039),
        ("s4", 0x003F),
    ]
]

# Setting up node links

# s1
SIMPLE_NODES[1].ports = [
    None,       # 0 - None
    None,       # 1 - Local (?)
    SIMPLE_NODES[2],   # 2 - s2
    None,       # 3 - None
    SIMPLE_NODES[3],   # 4 - s3
    None        # 5 - None
]

# s2
SIMPLE_NODES[2].ports = [
    None,       # 0 - None
    None,       # 1 - Local (?)
    SIMPLE_NODES[1],   # 2 - s1
    SIMPLE_NODES[3],   # 3 - s3
    None,       # 4 - None
    SIMPLE_NODES[4]    # 5 - s4
]

# s3
SIMPLE_NODES[3].ports = [
    None,       # 0 - None
    None,       # 1 - Local (?)
    SIMPLE_NODES[2],   # 2 - s2
    SIMPLE_NODES[4],   # 3 - s4
    SIMPLE_NODES[1],   # 4 - s1
    None        # 5 - None
]

# s4
SIMPLE_NODES[4].ports = [
    None,       # 0 - None
    None,       # 1 - Local (?)
    SIMPLE_NODES[3],   # 2 - s3
    None,       # 3 - None
    SIMPLE_NODES[2],   # 4 - s2
    None        # 5 - None
]

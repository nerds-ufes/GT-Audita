from urllib import request, error
import json

from script.tester import Polka, PolkaProbe
from script.utils import calc_digests, polka_route_ids, get_ingress_edge, calc_flow_id, hash_flow_id

ENDPOINT_URL = "http://localhost:5000/"
EDGE_NODE_ADDRESS = "0xf17f52151EbEF6C7334FAD080c5704D77216b732"

def call_deploy_flow_contract(flowId, first_host="h1", last_host="h10"):
    print(f"\n*** Deploying the contract related to the flowId {flowId}")

    data_dct = {
        "flowId": str(flowId),
        "routeId": str(polka_route_ids[first_host][last_host]),
        "edgeAddr": EDGE_NODE_ADDRESS
    }

    req = request.Request(
        ENDPOINT_URL + "deployFlowContract",
        data = json.dumps(data_dct).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res = request.urlopen(req)

    if(res.status == 201):
        print("Successfully deployed!")
        print("Transaction hash: " + res.read().decode('utf-8').strip(), end="\n\n")

def call_set_new_route(flowId, first_host, last_host):
    print(f"\n*** Setting new route to the flowId {flowId}")

    data_dct = {
        "flowId": str(flowId),
        "newRouteId": str(polka_route_ids[first_host][last_host]),
        "newEdgeAddr": EDGE_NODE_ADDRESS
    }

    req = request.Request(
        ENDPOINT_URL + "setRouteId",
        data = json.dumps(data_dct).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res = request.urlopen(req)

    if(res.status == 201):
        print("Successfully deployed!")
        print("Transaction hash: " + res.read().decode('utf-8').strip(), end="\n\n")

def call_set_ref_sig(pkt):
    polka_pkt = pkt.getlayer(Polka)
    assert polka_pkt is not None, "❌ Polka layer not found"
    probe_pkt = pkt.getlayer(PolkaProbe)
    assert probe_pkt is not None, "❌ Probe layer not found"

    ingress_edge = get_ingress_edge(pkt)
    flow_id = calc_flow_id(pkt)
    route_id = polka_pkt.route_id
    timestamp = probe_pkt.timestamp
    light_mult_sig = f"0x{calc_digests(route_id, ingress_edge, timestamp)[-1].hex()}"

    data_dct = {
        "flowId": str(flow_id),
        "routeId": str(route_id),
        "timestamp": str(hex(timestamp)),
        "lightMultSig": str(light_mult_sig),
    }

    req = request.Request(
        ENDPOINT_URL + "setRefSig",
        data = json.dumps(data_dct).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        res = request.urlopen(req)
        print("\n*** Registering reference signature in flow " + flow_id)
        print("Reference Signature: "  + data_dct["lightMultSig"])
        print("Transaction hash: " + res.read().decode('utf-8').strip(), end="\n\n")
    except error.HTTPError as e:
        if e.code == 500:
            print("\n*** Registering reference signature in flow " + flow_id)
            print("Erro: " + e.read().decode('utf-8'))        
    

def call_log_probe(pkt):
    polka_pkt = pkt.getlayer(Polka)
    assert polka_pkt is not None, "❌ Polka layer not found"
    probe_pkt = pkt.getlayer(PolkaProbe)
    assert probe_pkt is not None, "❌ Probe layer not found"

    flow_id = calc_flow_id(pkt)
    route_id = polka_pkt.route_id
    timestamp = probe_pkt.timestamp
    light_mult_sig = f"{probe_pkt.l_hash:#010x}"

    data_dct = {
        "flowId": str(flow_id),
        "routeId": str(route_id),
        "timestamp": str(hex(timestamp)),
        "lightMultSig": str(light_mult_sig),   
    }

    req = request.Request(
        ENDPOINT_URL + "logProbe",
        data = json.dumps(data_dct).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        res = request.urlopen(req)
        print("\n*** Logging probe signature in flow " + flow_id)
        print("Probe Signature: " + data_dct["lightMultSig"])
        print("Transaction hash: " + res.read().decode('utf8').strip(), end="\n\n")
    except error.HTTPError as e:
        if e.code == 500:
            print("\n*** Logging probe signature in flow " + flow_id)
            print("Erro: " + e.read().decode('utf-8'))

def call_get_flow_compliance(flowId):
    req = request.Request(
        ENDPOINT_URL + f"getFlowCompliance/{flowId}",
        headers={'Content-Type': 'application/json'}
    )

    try:
        res = request.urlopen(req)
        data = json.loads(res.read().decode('utf8'))
        print("\n*** Getting flow compliance of current route")
        print("FlowId: " + flowId)
        print("RouteId: " + data[1])
        print(f"Probe Success: {data[0]['success']}")
        print(f"Probe Fail: {data[0]['fail']}")
        print(f"Probe Null: {data[0]['nil']}\n\n")
    except error.HTTPError as e:
        if e.code == 500:
            print("\n*** Getting compliance of flow " + flowId)
            print("Erro: " + e.read().decode('utf-8'))

def call_get_flow_compliance_consolidation(flowId):
    req = request.Request(
        ENDPOINT_URL + f"getFlowSizeRoutesHistory/{flowId}",
        headers={'Content-Type': 'application/json'}
    )

    try:
        res = request.urlopen(req)
        data = json.loads(res.read().decode('utf8'))
        size = int(data[0])
        
        print("\n*** Getting flow compliance consolidation")
        print("FlowId: " + flowId)
        print(f"Qtt of routes in history: {size}")
        
        for i in range(0, size):
            req = request.Request(
                ENDPOINT_URL + f"getFlowCompliance/{flowId}/{i}",
                headers={'Content-Type': 'application/json'}
            )

            try:
                res = request.urlopen(req)
                data = json.loads(res.read().decode('utf8'))
                print("RouteId: " + data[1])
                print(f"Probe Success: {data[0]['success']}")
                print(f"Probe Fail: {data[0]['fail']}")
                print(f"Probe Null: {data[0]['nil']}\n\n")
            except error.HTTPError as e:
                if e.code == 500:
                    print(f"Erro(routeId[{i}]): " + e.read().decode('utf-8'))

    except error.HTTPError as e:
        if e.code == 500:
            print("\n*** Getting flow compliance consolidation " + flowId)
            print("Erro: " + e.read().decode('utf-8'))

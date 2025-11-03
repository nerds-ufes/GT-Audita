"""
Network tests
"""

import os.path as Path
from os import environ as Environ
from sys import path as sys_path
from time import sleep

from mn_wifi.bmv2 import P4Switch
from mn_wifi.net import info, Mininet

from scapy.all import Packet
from .scapy import Polka, PolkaProbe, start_sniffing

from .call_api import (
    call_deploy_flow_contract,
    call_set_ref_sig,
    hash_flow_id,
    call_log_probe,
    call_get_flow_compliance,
    call_get_flow_compliance_consolidation,
    call_set_new_route
) 

BMV2_TOOLS_PATH = Environ.get('BMV2_TOOLS_PATH')
if BMV2_TOOLS_PATH not in sys_path:
    sys_path.append(BMV2_TOOLS_PATH)

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.protocol import TMultiplexedProtocol

from .bm_runtime.standard import Standard
from .bm_runtime.standard.ttypes import *

def connect_to_switch(thrift_port, thrift_host='localhost'):
    """
    Conecta-se a um servidor Thrift do simple_switch (bmv2) e retorna o cliente e o transporte.
    Esta versão usa TMultiplexedProtocol para corrigir o erro.
    """
    print(f"Conectando ao switch (multiplexado) em {thrift_host}:{thrift_port}...")
    
    # 1. Cria o 'socket' e o 'transport'
    transport = TSocket.TSocket(thrift_host, thrift_port)
    transport = TTransport.TBufferedTransport(transport)
    
    # 2. Cria o 'protocol' base (binário)
    base_protocol = TBinaryProtocol.TBinaryProtocol(transport)
    
    # 3. CRIA O 'PROTOCOL' MULTIPLEXADO (A CORREÇÃO)
    #    Nós "envelopamos" o protocolo base e especificamos o nome do serviço
    #    Para o simple_switch (Standard.py), o nome do serviço é "standard"
    protocol = TMultiplexedProtocol.TMultiplexedProtocol(base_protocol, "standard")
                                                         
    # 4. Cria o Cliente (usando o protocolo multiplexado)
    client = Standard.Client(protocol)
    
    try:
        # 5. Abre a conexão
        transport.open()
        print("Conexão estabelecida com sucesso.")
        return client, transport
    
    except Thrift.TException as tx:
        print(f"Erro ao conectar ao switch na porta {thrift_port}: {tx.message}")
        return None, None

def disconnect_from_switch(transport):
    """Fecha a conexão de transporte."""
    if transport:
        print("Fechando conexão com o switch.")
        transport.close()

def ifaces_fn(net: Mininet, port):
    import re
    iname = re.compile(rf"e\d+-eth{port}")
    return [
        iface
        for switch in net.switches
        for iface in switch.intfNames()
        if iname.match(iface)
    ]

def sniff_cb(pkt: Packet):
    assert pkt.sniffed_on is not None, (
        "❌ Packet not sniffed on any interface. WTF."
    )
    polka = pkt.getlayer(Polka)
    assert polka is not None, "❌ Polka layer not found"
    probe = pkt.getlayer(PolkaProbe)
    assert probe is not None, "❌ PolkaProbe layer not found"
    eth = pkt.getlayer("Ether")
    assert eth is not None, "❌ Ether layer not found"
    icmp = pkt.getlayer("ICMP")
    assert icmp is not None, "❌ ICMP layer not found"

    if (icmp.type == 8):
        if(probe.timestamp == probe.l_hash):
            call_set_ref_sig(pkt)
        else:
            call_log_probe(pkt)

def integrity(net: Mininet, flows):
    """
    Integrity of the network
    """

    menu = """
*** (1)-Send Probe
*** (2)-Compliance
*** (3)-Compliance Consolidation
*** (4)-Change Route
*** (5)-Exit
"""

    def print_flows(f):
        for idx, flow in f.items():
            host_src = flow["host_src"]
            host_dst = flow["host_dst"]
            print(f"    *** ({idx})-Flow (from {host_src} -> to {host_dst})")

    while(1):
        action = input(menu + "\n--- Action: ")

        if action == "1":
            print("\n*** Choose flow to audit:")
            print_flows(flows) 
            print(f"    *** ({len(flows)})-All flows")
            idx_flow = input("--- Flow: ")
            rate = input("--- -i(seconds): ")
            qtt_probes = input("--- -c(qtt): ")

            try:
                int(idx_flow)
                float(rate)
                float(qtt_probes)

                if idx_flow == str(len(flows)):
                    for flow in flows.values():
                        host_src = net.get(flow["host_src"])
                        ip_dst = flow["ip_dst"]
                        host_src.cmd(f"ping -i {rate} -c {qtt_probes} {ip_dst} &")

                elif idx_flow in flows:
                    host_src = net.get(flows[idx_flow]["host_src"])
                    ip_dst = flows[idx_flow]["ip_dst"]
                    host_src.cmd(f"ping -i {rate} -c {qtt_probes} {ip_dst} &")

                else:
                    print("*** Invalid value of Flow")

            except ValueError:
                print("*** Invalid values of Flow/-i/-w")

        elif action == "2":
            print("\n*** Chose the flow")
            print_flows(flows)
            print(f"    *** ({len(flows)})-All flows")
            idx_flow = input("--- Flow: ")

            if idx_flow == str(len(flows)):
                for flow in flows.values():
                    call_get_flow_compliance(flow["flow_id"])
            
            elif idx_flow in flows:
                call_get_flow_compliance(flows[idx_flow]["flow_id"])
            
            else:
                print("*** Invalid value of Flow")

        elif action == "3":
            print("\n*** Chose the flow")
            print_flows(flows)
            idx_flow = input("--- Flow: ")
            
            if idx_flow in flows:
                call_get_flow_compliance_consolidation(flows[idx_flow]["flow_id"])
                call_get_flow_compliance(flows[idx_flow]["flow_id"])
            else:
                print("*** Invalid value of Flow")

        elif action == "4":
            print("\n*** Chose the flow")
            print_flows(flows)
            idx_flow = input("--- Flow: ")

            if idx_flow in flows:
                flow = flows[idx_flow]
                i = 0
                for route_idx, route_id in flow["routes"].items():
                    print(f"    *** ({route_idx})-{route_id}")
                    i+=1
                route_idx = input("\n--- Route: ")
                
                if route_idx in flow["routes"]:
                    if flow["current_route"] != flow["routes"][route_idx]:
                        route_id = flow["routes"][route_idx]
                        host_src = net.get(flow["host_src"])
                        host_dst = net.get(flow["host_dst"])
                        
                        client, transport = connect_to_switch(flow["thrift_port"])
                        if client:
                            entries = client.bm_mt_get_entries(0, "MyIngress.TunnelEncap.tunnel_encap_process_sr")
                            handle_encontrado = None
                            for entry in entries:
                                # entry.match_key é uma lista de objetos BmMatchParam
                                # Precisamos extrair o IP dela
                                match_key = entry.match_key[0]

                                # O objeto 'match_key' tem tipos diferentes (exato, lpm, ternário)
                                # No seu caso, é 'lpm' (Longest Prefix Match)
                                if match_key.type == BmMatchParamType.LPM:
                                    prefix = match_key.lpm.key
                                    prefix_len = match_key.lpm.prefix_length
                                    
                                    # O 'prefix' é retornado em bytes. Precisamos decodificar.
                                    # IPs são 4 bytes.
                                    import socket
                                    # :4 seleciona os 4 bytes do IP
                                    ip_addr = socket.inet_ntoa(prefix[:4])
                                    ip_str_com_prefixo = f"{ip_addr}/{prefix_len}"
                                    
                                    # 3. VERIFICAR SE É A ROTA QUE QUEREMOS
                                    if ip_addr == host_dst.IP():
                                        handle_encontrado = entry.entry_handle
                                        print(f"!!! Handle encontrado para {host_dst.IP()}: {handle_encontrado}")
                                        break # Achamos, saia do loop           
                            if handle_encontrado is not None:
                                print(f"Modificando a entrada com handle {handle_encontrado}...") 
                                # 6, 1, "00:00:00:00:01:01", 12345
                                # Você precisa converter isso para bytes.
                                new_action_params = [
                                    (6).to_bytes(2, 'big'),
                                    (1).to_bytes(1, 'big'),
                                    bytes.fromhex(host_dst.MAC().replace(':', '')),
                                    (route_id).to_bytes(8, 'big') # Assumindo 8 bytes
                                ]
                                client.bm_mt_modify_entry(
                                    0,
                                    "MyIngress.TunnelEncap.tunnel_encap_process_sr",
                                    handle_encontrado,
                                    "MyIngress.TunnelEncap.add_sourcerouting_header",
                                    new_action_params
                                )

                                flow["current_route"] = route_id
                                call_set_new_route(flow["flow_id"], route_id)

                            else:
                                print(f"Nenhuma entrada encontrada para {host_dst.IP()}.")
                    else:
                        print("*** This route is the currente route")
                else:
                    print("*** Invalid Route")
            else:
                print("*** Invalid Flow")
        elif action == "5":
            break
        else:
            print("*** Invalid action")

def linear(case):
    
    ADDITION = 2
    PARTIAL_DETOUR = 3
    COMPLETE_DETOUR = 4
    OUTOFORDER = 5
    SKIPPING = 6
    
    from ..linear_topology.topology import (
    CORE_THRIFT_CORE_OFFSET,
    LINK_SPEED,
    linear_topology,
    polka_json_path,
    )
    from ..linear_topology.flows import flows as linear_flows

    info("*** LINEAR TOPOLOGY ***\n")

    net = linear_topology(start=False)
    
    if case == ADDITION:
        info("*** ADDITION CASE ***\n")
        compromised, next_sw = net.switches[4:6]
        info(f"*** Replacing {compromised.name}'s links with compromised route\n")

        links = net.delLinkBetween(compromised, next_sw, allLinks=True)
        assert len(links) == 1, (
            f"❌ Expected 1 link to be removed between {compromised.name} and {next_sw.name}"
        )

        info("*** Adding attacker\n")
        attacker = net.addSwitch(
            "s555",
            netcfg=True,
            json=Path.join(polka_json_path, "polka-attacker.json"),
            thriftport=CORE_THRIFT_CORE_OFFSET + 555,
            loglevel="debug",
            cls=P4Switch,
        )
        info("*** Linking attacker\n")
        # Taking the "default" port #3 which route from s5 -> s6 should pass through on s5
        link = net.addLink(compromised, attacker, port1=3, port2=0, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")
        link = net.addLink(attacker, next_sw, port1=1, port2=2, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")

    elif case == PARTIAL_DETOUR:
        info("*** PARTIAL DETOUR CASE ***\n")

        prev_sw, skipped, next_sw = net.switches[4:7]
        info(f"*** Replacing {prev_sw.name}'s links with compromised route\n")

        links = net.delLinkBetween(prev_sw, skipped, allLinks=True)
        assert len(links) == 1, (
            f"❌ Expected 1 link to be removed between {prev_sw.name} and {skipped.name}"
        )
        links = net.delLinkBetween(next_sw, skipped, allLinks=True)
        assert len(links) == 1, (
            f"❌ Expected 1 link to be removed between {skipped.name} and {next_sw.name}"
        )

        info("*** Adding attacker\n")
        attacker = net.addSwitch(
            "s555",
            netcfg=True,
            json=Path.join(polka_json_path, "polka-attacker.json"),
            thriftport=CORE_THRIFT_CORE_OFFSET + 555,
            loglevel="debug",
            cls=P4Switch,
        )
        info("*** Linking attacker\n")
        # Taking the "default" port #3 which route from s5 -> s6 -> s7 should pass through on s6
        link = net.addLink(prev_sw, attacker, port1=3, port2=0, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")
        link = net.addLink(attacker, next_sw, port1=1, port2=4, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")
        # relink skipped sw
        link = net.addLink(prev_sw, skipped, port1=4, port2=2, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")
        link = net.addLink(skipped, next_sw, port1=4, port2=2, bw=LINK_SPEED)

    elif case == COMPLETE_DETOUR:

        info("*** COMPLETE DETOUR CASE ***\n")
        start_sw = net.switches[0]
        next_start_sw = net.switches[1]
        prev_last_sw = net.switches[8]
        last_sw = net.switches[9]
        info(f"*** Replacing {start_sw}'s links with compromised route\n")

        links = net.delLinkBetween(start_sw, next_start_sw, allLinks=True)
        assert len(links) == 1, (
            f"❌ Expected 1 link to be removed between {start_sw.name} and {next_start_sw.name}"
        )
        links = net.delLinkBetween(last_sw, prev_last_sw, allLinks=True)
        assert len(links) == 1, (
            f"❌ Expected 1 link to be removed between {prev_last_sw.name} and {last_sw.name}"
        )

        info("*** Adding attackers\n")
        s222_sw = net.addSwitch(
            "s222",
            netcfg=True,
            json=Path.join(polka_json_path, "polka-attacker.json"),
            thriftport=CORE_THRIFT_CORE_OFFSET + 222,
            loglevel="debug",
            cls=P4Switch,
        )
        link = net.addLink(start_sw, s222_sw, port1=2, port2=0, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")
        aux_sw = s222_sw

        for i in range(3, 10):
            attacker = net.addSwitch(
                f"s{i}{i}{i}",
                netcfg=True,
                json=Path.join(polka_json_path, "polka-attacker.json"),
                thriftport=CORE_THRIFT_CORE_OFFSET + i + i*10 + i*100,
                loglevel="debug",
                cls=P4Switch,
            )
            info("*** Linking attacker\n")
            
            if aux_sw:
                link = net.addLink(aux_sw, attacker, port1=1, port2=0, bw=LINK_SPEED)
                info(f"*** Created link {link}\n")
            aux_sw = attacker
        
        link = net.addLink(aux_sw, last_sw, port1=1, port2=2, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")

    elif case == OUTOFORDER:

        info("*** OUTOFORDER CASE ***\n")
        oor = net.switches[3:7]
        info("*** Replacing links with compromised route\n")

        for i in range(3):
            links = net.delLinkBetween(oor[i], oor[i + 1], allLinks=True)
            assert len(links) == 1, (
                f"❌ Expected 1 link to be removed between {oor[i].name} and {oor[i + 1].name}"
            )

        info("*** Linking back\n")
        # Taking the "default" port #3 which route from s4 -> s5 -> s6 should pass through on s5
        link = net.addLink(oor[0], oor[2], port1=3, port2=2, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")
        link = net.addLink(oor[2], oor[1], port1=3, port2=2, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")
        link = net.addLink(oor[1], oor[3], port1=3, port2=2, bw=LINK_SPEED)
        info(f"*** Created link {link}\n")

    elif case == SKIPPING:

        info("*** SKIPPING CASE ***\n")
        
        prev_sw, skipped, next_sw = net.switches[3:6]
        info(f"*** Replacing {skipped.name}'s links with compromised route\n")

        links = net.delLinkBetween(skipped, next_sw, allLinks=True)
        assert len(links) == 1, (
            f"❌ Expected 1 link to be removed between {skipped.name} and {next_sw.name}"
        )
        links = net.delLinkBetween(skipped, prev_sw, allLinks=True)
        assert len(links) == 1, (
            f"❌ Expected 1 link to be removed between {skipped.name} and {prev_sw.name}"
        )

        new_link = net.addLink(prev_sw, next_sw, port1=3, port2=2, bw=LINK_SPEED)
        info(f"*** Created link {new_link}\n")
    
    else:
        info("*** DEFAULT CASE ***\n")

    try:
        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)
        
        deploy_flow = input("--- Deploy flow[y/n]: ")
        if deploy_flow == "y":
            for flow in linear_flows.values():
                flow_id = hash_flow_id(
                    flow["ip_src"], 
                    flow["port_src"], 
                    flow["ip_dst"], 
                    flow["port_dst"]
                )
                flow["flow_id"] = flow_id
                call_deploy_flow_contract(flow_id, flow["current_route"])

        else:
            for flow in linear_flows.values():
                flow_id = hash_flow_id(
                    flow["ip_src"], 
                    flow["port_src"], 
                    flow["ip_dst"], 
                    flow["port_dst"]
                )
                flow["flow_id"] = flow_id

        sniff = start_sniffing(net, 2, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net, linear_flows)

        # Time to finish printing the logs
        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** LINEAR TOPOLOGY DONE ***\n")

    finally:
        net.stop()

    info("*** ✅ Run finished.\n")

def simple():

    from ..simple_topology.topology import simple_topology
    from ..simple_topology.flows import flows as simple_flows

    info("*** SIMPLE TOPOLOGY ***\n")

    net = simple_topology(start=False)
    try:
        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)
        
        deploy_flow = input("--- Deploy flow[y/n]: ")
        if deploy_flow == "y":
            for flow in simple_flows.values():
                flow_id = hash_flow_id(
                    flow["ip_src"], 
                    flow["port_src"], 
                    flow["ip_dst"], 
                    flow["port_dst"]
                )
                flow["flow_id"] = flow_id
                call_deploy_flow_contract(flow_id, flow["current_route"])

        else:
            for flow in simple_flows.values():
                flow_id = hash_flow_id(
                    flow["ip_src"], 
                    flow["port_src"], 
                    flow["ip_dst"], 
                    flow["port_dst"]
                )
                flow["flow_id"] = flow_id

        sniff = start_sniffing(net, 6, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net, simple_flows)

        # Time to finish printing the logs
        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** SIMPLE TOPOLOGY DONE ***\n")

    finally:
        net.stop()

    info("*** ✅ Run finished.\n")
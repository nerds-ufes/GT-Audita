"""
Network tests
"""

# import json
import os.path as Path
from time import sleep
# from typing import Iterable, TypeVar
# import urllib.request as request

# from mininet.log import info
from mn_wifi.bmv2 import (  # type: ignore assumes import exists, it's from p4-utils
    P4Switch,
)
from mn_wifi.net import info, Mininet
from scapy.all import Packet

from .scapy import Polka, PolkaProbe, start_sniffing
# from .thrift import set_crc_parameters_common
from .topo import (
    CORE_THRIFT_CORE_OFFSET,
    LINK_SPEED,
    # all_ifaces,
    # connect_to_core_switch,
    linear_topology,
    simple_topology,
    polka_json_path,
    # set_seed_e1,
    # set_seed_e10,
)
# from .calc_digests import calc_digests

from time import sleep

# from script.tester import linear_topology, Polka, PolkaProbe, integrity, start_sniffing
from script.call_api import call_deploy_flow_contract, call_set_ref_sig, hash_flow_id, call_log_probe, call_get_flow_compliance, call_get_flow_compliance_consolidation, call_set_new_route 
# from .utils import calc_digests

# T = TypeVar("T")

def ifaces_fn(net: Mininet):
    import re
    iname = re.compile(r"e\d+-eth2")
    
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
        #print(f"\nPacote capturado na interface: {pkt.sniffed_on}")
        #print(pkt.summary())
        if(probe.timestamp == probe.l_hash):
            call_set_ref_sig(pkt)
        else:
            call_log_probe(pkt)

def integrity(net: Mininet):
    """
    Test the integrity of the network, this is to be used in a suite of testsdicionando um novo host e um link para o switch s1 dinamicamentei
    """

    while(1):
        print("\n*** (1)-Send Probe\n*** (2)-Compliance\n*** (3)-Compliance Consolidation\n*** (4)-Change Route\n*** (5)-Exit")
        action = input("\n*** Action: ")
        print("\n\n")
        if action == "1":
            print("*** Sending Probe(s)")
            src_host_name = input("SRC host: ") 
            src_host = net.get(src_host_name)
            assert src_host is not None, "Host " + src_host_name + " not found"
         
            dst_host_name = input("DST host: ")
            dst_host = net.get(dst_host_name)  # h11 is right beside h1, so wouldn't traverse all switches
            assert dst_host is not None, "Host " + dst_host_name + " not found"
            
            num_probes = input("Number of probes: ")

            info(
                "\n*** Testing network integrity\n"
                f"    a ping from {src_host.name} to {dst_host.name},\n"
                "    goes through all core switches.\n"
            )
            
            src_host.cmd('ping -c ' + num_probes, dst_host.IP())
            sleep(int(num_probes)*15)
            
        elif action == "2" or action == "3" or action == "4":
            print("*** Chose the flow")
            src_host_name = input("SRC host: ")
            src_host = net.get(src_host_name)
            assert src_host is not None, "Host " + src_host_name + " not found"

            dst_host_name = input("DST host: ")
            dst_host = net.get(dst_host_name)  # h11 is right beside h1, so wouldn't traverse all switches
            assert dst_host is not None, "Host " + dst_host_name + " not found"
            
            print(f"{src_host}({src_host.IP()}) --> {dst_host}({dst_host.IP()})")

            if action == "3":
                call_get_flow_compliance_consolidation(hash_flow_id(src_host.IP(), "0", dst_host.IP(), "0"))

            elif action == "4":
                routeId = input("New routeId: ")
                call_set_new_route(hash_flow_id(src_host.IP(), "0", dst_host.IP(), "0"), routeId)
    
            if action == "2" or action == "3":
                call_get_flow_compliance(hash_flow_id(src_host.IP(), "0", dst_host.IP(), "0"))

            sleep(2)

        elif action == "5":
            break

def default():
    """
    Collect the hashes (all intermediary) from the network
    """

    info("*** Starting run for collecting hash and intermediaries\n")

    net = linear_topology(start=False)
    try:
        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)
        
        call_deploy_flow_contract(hash_flow_id("10.0.1.1", "0", "10.0.10.10", "0"))
        call_deploy_flow_contract(hash_flow_id("10.0.10.10", "0", "10.0.1.1", "0"))

        sniff = start_sniffing(net, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net)

        # Time to finish printing the logs
        sleep(2)  

        info("\n*** Stopping sniffing\n")
        sniff.stop()

        info("*** Hashes collected ***\n")

    finally:
        net.stop()

    info("*** ✅ Run finished.\n")

def addition():
    """
       Test if the network is protected against an addition attack

       An addition attack is when a new switch is added to the network between two existing switches,
       and the existing connections of surrounding switches = linear_topology()
    are not touched.
    """

    info("*** ADDITION TEST ***\n")
    net = linear_topology(start=False)
    try:
        # Switch ports
        # Generally, on core POV:
        # eth0 = lo?
        # eth1 = edge
        # eth2 = previous
        # eth3 = next
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
        # net.addLink(compromised, attacker, bw=LINK_SPEED)
        # net.addLink(attacker, next_sw, bw=LINK_SPEED)

        # The "next" is now port #4, which is mostly unused
        # The attacker will take the port #3 instead.
        # This is still used in traffic in the s6 -> s5 -> s4 direction
        # new_link = net.addLink(compromised, next_sw, port1=4, port2=2, bw=LINK_SPEED)
        # info(f"*** Created link {new_link}\n")

        # net = set_seed_e1(net, 0xABADCAFE)
        # net = set_seed_e10(net, 0xBADDC0DE)

        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)

        # CLI(net)

        #call_deploy_flow_contract(hash_flow_id("10.0.1.1", "0", "10.0.10.10", "0"))
        #call_deploy_flow_contract(hash_flow_id("10.0.10.10", "0", "10.0.1.1", "0"))

        sniff = start_sniffing(net, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net)

        # Time to finish printing the logs
        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** ADDITION TEST DONE ***\n")

    finally:
        net.stop()

def partial_detour():
    """
    Test if the network is protected against a detour attack.

    A detour attack is when a new switch is added to the network between two existing switches,
    concurring with an existing switch, with the same connections as the existing switch.
    """
    info("*** PARTIAL DETOUR TEST ***\n")
    net = linear_topology(start=False)
    try:
        # Switch ports
        # Generally, on core POV:
        # eth0 = lo?
        # eth1 = edge
        # eth2 = previous
        # eth3 = next
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

        # net = set_seed_e1(net, 0xBADDC0DE)
        # net = set_seed_e10(net, 0xDEADBEEF)

        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)

        # CLI(net)

        #call_deploy_flow_contract(hash_flow_id("10.0.1.1", "0", "10.0.10.10", "0"))
        #call_deploy_flow_contract(hash_flow_id("10.0.10.10", "0", "10.0.1.1", "0"))

        sniff = start_sniffing(net, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net)

        # Time to finish printing the logs
        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** PARTIAL DETOUR TEST DONE ***\n")

    finally:
        net.stop()

def complete_detour():
    """
    Test if the network is protected against a detour attack.

    A detour attack is when a new switch is added to the network between two existing switches,
    concurring with an existing switch, with the same connections as the existing switch.
    """
    info("*** COMPLETE DETOUR TEST ***\n")
    net = linear_topology(start=False)
    try:
        # Switch ports
        # Generally, on core POV:
        # eth0 = lo?
        # eth1 = edge
        # eth2 = previous
        # eth3 = next
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

        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)

        # CLI(net)

        #call_deploy_flow_contract(hash_flow_id("10.0.1.1", "0", "10.0.10.10", "0"))
        #call_deploy_flow_contract(hash_flow_id("10.0.10.10", "0", "10.0.1.1", "0"))

        sniff = start_sniffing(net, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net)

        # Time to finish printing the logs
        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** COMPLETE DETOUR TEST DONE ***\n")

    finally:
        net.stop()

def outoforder():
    """
    Test if the network is protected against an outoforder attack.

    An outoforder attack is when the route is acessed using all defined router,
     and no other routers, but their order differ.
    """
    info("*** OUTOFORDER TEST ***\n")
    net = linear_topology(start=False)
    try:
        # Switch ports
        # Generally, on core POV:
        # eth0 = lo?
        # eth1 = edge
        # eth2 = previous
        # eth3 = next
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

        # net = set_seed_e1(net, 0xABADCAFE)
        # net = set_seed_e10(net, 0xBADDC0DE)

        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)

        # CLI(net)

        # call_deploy_flow_contract(hash_flow_id("10.0.1.1", "0", "10.0.10.10", "0"))
        # call_deploy_flow_contract(hash_flow_id("10.0.10.10", "0", "10.0.1.1", "0"))

        sniff = start_sniffing(net, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net)

        # Time to finish printing the logs
        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** OUT OF ORDER TEST DONE ***\n")

    finally:
        net.stop()

def skipping():
    """
    Test if the network is protected against a skipping attack.

    A skipping attack is when a route skips the core entirely and goes directly to the edge.
    """

    info("*** SKIPPING TEST ***\n")
    net = linear_topology(start=False)
    try:
        # Switch ports
        # Generally, on core POV:
        # eth0 = lo?
        # eth1 = edge
        # eth2 = previous
        # eth3 = next
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

        # net = set_seed_e1(net, 0x61E8D6E7)
        # net = set_seed_e10(net, 0xABADCAFE)

        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)

        # CLI(net)

        #call_deploy_flow_contract(hash_flow_id("10.0.1.1", "0", "10.0.10.10", "0"))
        #call_deploy_flow_contract(hash_flow_id("10.0.10.10", "0", "10.0.1.1", "0"))

        sniff = start_sniffing(net, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net)

        # Time to finish printing the logs
        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** SKIPPING TEST DONE ***\n")

    finally:
        net.stop()

def simple():
    PATH1_H1_H4 = 89931881502587 
    PATH1_H4_H1 = 89931881502584

    PATH2_H1_H4 = 166807723460375
    PATH2_H4_H1 = 42207349362690

    PATH3_H1_H4 = 18205742658938488364
    PATH3_H4_H1 = 2908909522564514583

    info("*** SIMPLE TEST ***\n")
    net = simple_topology(start=False)
    try:
        # Switch ports
        # Generally, on core POV:
        # eth0 = lo?
        # eth1 = edge

        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)

        # CLI(net)

        call_deploy_flow_contract(flowId=hash_flow_id("10.0.1.1", "0", "10.0.4.4", "0"), routeId=PATH1_H1_H4)
        call_deploy_flow_contract(flowId=hash_flow_id("10.0.4.4", "0", "10.0.1.1", "0"), routeId=PATH1_H4_H1)

        sniff = start_sniffing(net, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net)

        # Time to finish printing the logs
        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** SIMPLE TEST DONE ***\n")

    finally:
        net.stop()

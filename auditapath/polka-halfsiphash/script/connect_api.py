from mn_wifi.net import info, Mininet
from time import sleep
from scapy.all import Packet

from script.tester import linear_topology, Polka, PolkaProbe, integrity, start_sniffing
from script.call_api import call_deploy_flow_contract, call_set_ref_sig, hash_flow_id, call_log_probe, call_get_flow_compliance, call_get_flow_compliance_consolidation, call_set_new_route 
from .utils import calc_digests

def integrity(net: Mininet):
    """
    Test the integrity of the network, this is to be used in a suite of tests
    """

    while(1):
        print("*** (1)-Send Probe\n*** (2)-Compliance\n*** (3)-Compliance Consolidation\n*** (4)-Change Route\n*** (5)-Exit")
        action = input("\n*** Action: ")
        print("\n\n")
        if action == "1":
            print("*** Sending Probe(s)")
            first_host_name = input("First host: ") 
            first_host = net.get(first_host_name)
            assert first_host is not None, "Host " + first_host_name + " not found"
         
            last_host_name = input("Last host: ")
            last_host = net.get(last_host_name)  # h11 is right beside h1, so wouldn't traverse all switches
            assert last_host is not None, "Host " + last_host_name + " not found"
            
            num_probes = input("Number of probes: ")

            info(
                "\n*** Testing network integrity\n"
                f"    a ping from {first_host.name} to {last_host.name},\n"
                "    goes through all core switches.\n"
            )
            
            first_host.cmd('ping -c ' + num_probes, last_host.IP())
            sleep(int(num_probes)*6)
            
        elif action == "2" or action == "3" or action == "4":
            print("*** Chose the flow")
            first_host_name = input("First host: ")
            first_host = net.get(first_host_name)
            assert first_host is not None, "Host " + first_host_name + " not found"

            last_host_name = input("Last host: ")
            last_host = net.get(last_host_name)  # h11 is right beside h1, so wouldn't traverse all switches
            assert last_host is not None, "Host " + last_host_name + " not found"
            
            print(f"{first_host}({first_host.IP()}) --> {last_host}({last_host.IP()})")

            if action == "3":
                call_get_flow_compliance_consolidation(hash_flow_id(first_host.IP(), "0", last_host.IP(), "0"))

            elif action == "4":
                call_set_new_route(hash_flow_id(first_host.IP(), "0", last_host.IP(), "0"), first_host_name, last_host_name)
    
            if action == "2" or action == "3":
                call_get_flow_compliance(hash_flow_id(first_host.IP(), "0", last_host.IP(), "0"))

            sleep(2)



        elif action == "5":
            break

def connect_api():
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

            if(probe.timestamp == probe.l_hash):
                call_set_ref_sig(pkt)
            else:
                call_log_probe(pkt)

            # print(f"{pkt.time} : {pkt.sniffed_on} - {eth.src} -> {eth.dst} => {probe.l_hash:#0{10}x}")

        
        call_deploy_flow_contract(hash_flow_id("10.0.1.1", "0", "10.0.10.10", "0"))
        #call_deploy_flow_contract(hash_flow_id("10.0.10.10", "0", "10.0.1.1", "0"))

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

def get_hashes_hops():
    """
        Return hash at each hop
    """

    info("*** Starting run for collecting hash and intermediaries\n")

    net = linear_topology(start=False)
    try:
        net.start()
        net.staticArp()

        # sleep for a bit to let the network stabilize
        sleep(3)

        def ifaces_fn(net: Mininet):
            return ["e1-eth2", "s1-eth2", "s2-eth3", "s3-eth3", "s4-eth3", "s5-eth3", "s6-eth3", "s7-eth3", "s8-eth3", "s9-eth3", "s10-eth1", "e10-eth2"]

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


            if probe.timestamp == probe.l_hash:
                import re 
                pattern = r"\S\d+"
                match = re.search(pattern, pkt.sniffed_on)
                
                if match:
                    print(f"Reference Signature: 0x{calc_digests(polka.route_id, match.group(), probe.timestamp)[-1].hex()}")
                
            print(f"{hex(probe.timestamp)} : {pkt.sniffed_on} - {eth.src} -> {eth.dst} : => {probe.l_hash:#0{10}x}")

        sniff = start_sniffing(net, ifaces_fn=ifaces_fn, cb=sniff_cb)

        integrity(net)

        sleep(2)

        info("*** Stopping sniffing\n")
        sniff.stop()

        info("*** Hashes collected ***\n")

    finally:
        net.stop()

    info("*** ✅ Run finished.\n")

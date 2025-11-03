
import polka_halfsiphash.script.scenarios as scenarios
from mininet.log import setLogLevel, info, debug

if __name__ == "__main__":

    setLogLevel("info")
    
    topology_menu = """
*** (1)-Simple
*** (2)-Linear
"""

    case_menu = """
*** (1)-Default
*** (2)-Addition
*** (3)-Partial Detour
*** (4)-Complete Detour
*** (5)-Skipping
*** (6)-Out of Order
"""

    topology = input(topology_menu + "\n--- Topology: ")

    if topology == "1":
        scenarios.simple()
    
    elif topology == "2":
        case = input(case_menu + "\n--- Case: ")
        try:
            case = int(case)
            if (case > 0 and case < 7):
                scenarios.linear(case)
            else:
                print("*** Invalid case!\n")
        except ValueError:
            print("*** Invalid case!\n")
    else:
        print("*** Invalid topology!\n")

import polka_halfsiphash.script.scenarios as scenarios

if __name__ == "__main__":
    
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

    topology = input(topology_menu + "\n*** Topology: ")

    if topology == "1":
        scenarios.simple()
    
    elif topology == "2":
    
        case = input(case_menu + "\n*** Case: ")

        if case == "1":
            scenarios.default()

        elif case == "2":
            scenarios.addition()

        elif case == "3":
            scenarios.partial_detour()

        elif case == "4":
            scenarios.complete_detour()

        elif case == "5":
            scenarios.skipping()

        elif case == "6":
            scenarios.outoforder()

        else:
            print("Invalid case!\n")
    
    else:
        print("Invalid topology!\n")

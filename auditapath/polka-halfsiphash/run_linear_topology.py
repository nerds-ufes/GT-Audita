#!/usr/bin/python3
# Copyright [2019-2022] Universidade Federal do Espirito Santo
#                       Instituto Federal do Espirito Santo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# https://mininet.org/api/hierarchy.html
from mininet.log import setLogLevel, info, debug

import script.tester as tester

if __name__ == "__main__":
    setLogLevel("info")
    
    print("\n*** (1)-Default\n*** (2)-Addition\n*** (3)-Partial Detour\n*** (4)-Complete Detour\n*** (5)-Skipping\n*** (6)-Out of Order\n")
    case = input("*** Case: ")

    if case == "1":
        tester.default()

    elif case == "2":
        tester.addition()

    elif case == "3":
        tester.partial_detour()

    elif case == "4":
        tester.complete_detour()
    
    elif case == "5":
        tester.skipping()

    elif case == "6":
        tester.outoforder()

    else:
        print("Invalid case!\n")

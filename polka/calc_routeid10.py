#!/usr/bin/env python3
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

from polka.tools import calculate_routeid, print_poly
DEBUG = False


def _main():
    print("Insering irred poly (node-ID)")
    s = [
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1],  # s1
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1],  # s2
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1],  # s3
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],  # s4
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1],  # s5
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1],  # s6
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1],  # s7
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1],  # s8
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1],  # s9
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1],  # s10
    ]
    print("From h2 to h10 ====")
    # defining the nodes from h2 to h10
    nodes = [
        s[1],
        s[2],
        s[3],
        s[4],
        s[5],
        s[6],
        s[7],
        s[8],
        s[9],
    ]
    # defining the transmission state for each node from h1 to h3
    o = [
        [1, 1],     # s2
        [1, 1],     # s3
        [1, 1],     # s4
        [1, 1],     # s5
        [1, 1],     # s6
        [1, 1],     # s7
        [1, 1],     # s8
        [1, 1],     # s9
        [1],        # s10
    ]
    print_poly(calculate_routeid(nodes, o, debug=DEBUG))

    print("From h10 to h2 ====")
    # defining the nodes from h10 to h2
    nodes = [
        s[9],
        s[8],
        s[7],
        s[6],
        s[5],
        s[4],
        s[3],
        s[2],
        s[1],
    ]
    # defining the transmission state for each node from h1 to h3
    o = [
        [1, 0],     # s10
        [1, 0],     # s9
        [1, 0],     # s8
        [1, 0],     # s7
        [1, 0],     # s6
        [1, 0],     # s5
        [1, 0],     # s4
        [1, 0],     # s3
        [1],        # s2
    ]

    print_poly(calculate_routeid(nodes, o, debug=DEBUG))


if __name__ == '__main__':
    _main()
#! /usr/bin/env python3
# 
# This file is part of the ServiceDiscovery distribution.
# Copyright (c) 2023 Javier Moreno Garcia.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import ServiceDiscovery
import argparse
import sys

def main():


    parser = argparse.ArgumentParser(description="Service discovery client")
    parser.add_argument(
        "service_name",
        nargs=1,
        help="Service name",
        type=str)
    parser.add_argument(
        '-t',
        required=False,
        default=3,
        help='timeout',
        type=int)
    parser.add_argument(
        '-r',
        required=False,
        default=-1,
        help='retries',
        type=int)
    args = parser.parse_args(sys.argv[1:])


    client = ServiceDiscovery.client()
    try:
        ip = client.getServiceIP(args.service_name[0], args.t, args.r)
        print(ip)

    except KeyboardInterrupt:
        pass


# Main execution
if __name__ == '__main__':
    main()

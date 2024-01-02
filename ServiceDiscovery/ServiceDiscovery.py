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


import socket
import struct
import threading
import time
import ServiceDiscoveryLocal


version = "0.1.0"


class constants():
    MCAST_DISCOVER_GRP = '224.1.1.1'
    MCAST_DISCOVER_SERVER_PORT = 5005
    MCAST_DISCOVER_CLIENT_PORT = 5006
    MULTICAST_TTL = 2
    DISCOVER_MSG_REQUEST = "Who's SERVICE?"
    DISCOVER_MSG_RESPONSE = "I'm SERVICE"
    SERVICE_LABEL = "SERVICE"


class container:
    pass


class daemon():

    def __init__(self, service_name):
        self.__thread = None
        self.__shared_container = container()
        self.__shared_container.run = True
        self.__shared_container.service_name = service_name
        self.__shared_container.mcast_listen_request = ServiceDiscoveryLocal.mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SERVER_PORT)
        self.__shared_container.mcast_send_respond = ServiceDiscoveryLocal.mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_CLIENT_PORT)


    def __del__(self):
        self.stop()
        if self.__thread:
            self.__thread.join()


    def __run(shared_container):

        expected_request = constants.DISCOVER_MSG_REQUEST.replace(constants.SERVICE_LABEL, shared_container.service_name).encode()
        response = constants.DISCOVER_MSG_RESPONSE.replace(constants.SERVICE_LABEL, shared_container.service_name).encode()


        while shared_container.run:
            request, ip, port = shared_container.mcast_listen_request.read()
            if not request:
                break

            if request == expected_request:
                shared_container.mcast_send_respond.send(response)


    def run(self, thread=False):
        if thread:
            self.__thread  = threading.Thread(target=daemon.__run, daemon=True, args=[self.__shared_container])
            self.__thread .start()
            return self.__thread
        else:
            daemon.__run(self.__mcast)
            return None


    def stop(self):
        self.__shared_container.run = False
        self.__shared_container.mcast_listen_request.close()
        self.__shared_container.mcast_send_respond.close()


class client():

    def getServiceIP(self, service_name, timeout=5, retry=3) -> str:
        mcast_send_request = ServiceDiscoveryLocal.mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SERVER_PORT)
        mcast_listen_respond = ServiceDiscoveryLocal.mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_CLIENT_PORT)

        request = constants.DISCOVER_MSG_REQUEST.replace(constants.SERVICE_LABEL, service_name).encode()
        expected_response = constants.DISCOVER_MSG_RESPONSE.replace(constants.SERVICE_LABEL, service_name).encode()

        i = 0

        while True:

            i += 1

            mcast_send_request.send(request)
            received_response, ip, port = mcast_listen_respond.read(timeout)

            if received_response == expected_response:
                return ip

            elif i >= retry:
                return None

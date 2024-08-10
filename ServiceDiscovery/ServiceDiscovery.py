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

import os
import socket
import struct
import threading
import time
import random
import re


version = "0.2.2"


class constants():
    MCAST_DISCOVER_GRP = '224.1.1.1'
    MCAST_DISCOVER_SERVER_PORT = 5005
    MCAST_DISCOVER_CLIENT_PORT = 5006
    MCAST_DISCOVER_SYNC_PORT = 5007
    MCAST_DISCOVER_SYNC_TIME = 0.25
    MULTICAST_TTL = 2
    DISCOVER_MSG_REQUEST = "Who's SERVICE?"
    DISCOVER_MSG_RESPONSE = "I'm SERVICE"
    SERVICE_LABEL = "SERVICE"


class mcast():

    def __init__(self, ip, port):
        self.__ip = ip
        self.__port = port
        self.__open = True
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if os.name != 'nt':
            self.__sock.bind((ip, port))
        else:
            self.__sock.bind(('', port))
        self.__sock.settimeout(0.1)

        mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
        self.__sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


    def __del__(self):
        self.close()


    def read(self, timeout=-1):

        current_epoch_time = float(time.time())
        while self.__open:
            try:
                data, (ip, port) = self.__sock.recvfrom(4096)
                return data, ip, port

            except socket.timeout:
                if timeout >= 0 and float(time.time()) - current_epoch_time >= timeout:
                    return None, None, None

            except socket.error:
                return None, None, None


        return None, None, None


    def send(self, msg):
        if isinstance(msg, str):
            msg = msg.encode()
        self.__sock.sendto(msg, (self.__ip, self.__port))


    def close(self):
        self.__open = False
        self.__sock.close()


class container:
    pass


class daemon():

    def __init__(self, service_name):
        self.__thread = None
        self.__shared_container = container()
        self.__shared_container.run = True
        self.__shared_container.service_name = service_name
        self.__shared_container.mcast_listen_request = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SERVER_PORT)
        self.__shared_container.mcast_send_respond = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_CLIENT_PORT)
        self.__shared_container.mcast_sync = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SYNC_PORT)
        self.__shared_container.sync_token = int(random.random() * 1000000) + 1


    def __del__(self):
        self.stop()
        if self.__thread:
            self.__thread.join()


    def __readSync(shared_container):

        while True:
            received_response, ip, port = shared_container.mcast_sync.read(constants.MCAST_DISCOVER_SYNC_TIME)

            if not received_response:
                return None

            elif re.match("^" + shared_container.service_name + "\.\d*$", received_response.decode()):
                return int(received_response.decode().split(".")[1])


    def __run(shared_container):

        expected_request = constants.DISCOVER_MSG_REQUEST.replace(constants.SERVICE_LABEL, shared_container.service_name).encode()
        response = constants.DISCOVER_MSG_RESPONSE.replace(constants.SERVICE_LABEL, shared_container.service_name).encode()


        while shared_container.run:
            request, ip, port = shared_container.mcast_listen_request.read()
            if not request:
                break

            if request == expected_request:

                # Sync process
                shared_container.mcast_sync.send(str(shared_container.service_name + "." + str(shared_container.sync_token)).encode())
                main_token = True
                while True:

                    sync_token = daemon.__readSync(shared_container)
                    if sync_token == None:
                        break

                    elif sync_token < shared_container.sync_token:
                        main_token = False


                # Respose if main
                if main_token:
                    shared_container.sync_token = 0
                    shared_container.mcast_send_respond.send(response)


    def run(self, thread=False):
        if thread:
            self.__thread  = threading.Thread(target=daemon.__run, daemon=True, args=[self.__shared_container])
            self.__thread .start()
            return self.__thread
        else:
            daemon.__run(self.__shared_container)
            return None


    def stop(self):
        self.__shared_container.run = False
        self.__shared_container.mcast_listen_request.close()
        self.__shared_container.mcast_send_respond.close()


    def isMaster(self):
        return self.__shared_container.sync_token == 0


class client():

    def getServiceIP(self, service_name, timeout=5, retry=0) -> str:
        mcast_send_request = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SERVER_PORT)
        mcast_listen_respond = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_CLIENT_PORT)

        request = constants.DISCOVER_MSG_REQUEST.replace(constants.SERVICE_LABEL, service_name).encode()
        expected_response = constants.DISCOVER_MSG_RESPONSE.replace(constants.SERVICE_LABEL, service_name).encode()

        i = 0

        while retry < 0 or i <= retry:

            mcast_send_request.send(request)
            received_response, ip, port = mcast_listen_respond.read(timeout)

            if received_response == expected_response:
                return ip

            i += 1

        return None

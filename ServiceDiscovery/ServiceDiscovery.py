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


version = "0.4.1"


class constants():
    MCAST_DISCOVER_GRP = '224.1.1.1'
    MCAST_DISCOVER_SERVER_PORT = 5005
    MCAST_DISCOVER_SYNC_PORT = 5007
    MCAST_SYNC_READ_TIME = 0.5
    MCAST_SYNC_SEND_TIME = 0.5
    READ_OWN_MAX_COUNT = 3
    DISCOVER_MSG_REQUEST = "Who's SERVICE?"
    DISCOVER_MSG_RESPONSE = "I'm SERVICE"
    SERVICE_LABEL = "SERVICE"
    PORT_SEP = b'#'
    SYNC_SEP = b'.'
    MTU = 1500


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
        try:
            self.__sock.sendto(msg, (self.__ip, self.__port))
            return True

        except:
            return False


    def close(self):
        self.__open = False
        self.__sock.close()


class udpRandomPortListener():

    def __init__(self):
        super().__init__()
        self.__open = True
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(('', 0))
        self.__sock.settimeout(0.1)


    def __del__(self):
        self.close()


    def read(self, timeout=-1):

        current_epoch_time = int(time.time())
        while self.__open:
            try:
                data, (ip, port) = self.__sock.recvfrom(constants.MTU)
                return data, ip, port

            except socket.timeout:
                if timeout >= 0 and int(time.time()) - current_epoch_time >= timeout:
                    return None, None, None

            except socket.error:
                return None, None, None

        return None, None, None


    def send(self, ip, port, msg):
        if isinstance(msg, str):
            msg = msg.encode()

        chn_msg = [msg[idx : idx + constants.MTU] for idx in range(0, len(msg), constants.MTU)]

        for chn in chn_msg:
            self.__sock.sendto(chn, (ip, port))


    @property
    def port(self):
        return self.__sock.getsockname()[1]


    def close(self):
        self.__open = False
        self.__sock.close()


class udpClient():
    def __init__(self, ip, port):
        self.__open = True
        self.__remote_ip = ip
        self.__remote_port = port
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.settimeout(0.1)


    def __del__(self):
        self.close()


    def read(self, timeout=-1):

        current_epoch_time = int(time.time())
        while self.__open:
            try:
                data = self.__sock.recv(constants.MTU)
                return data

            except socket.timeout:
                if timeout >= 0 and int(time.time()) - current_epoch_time >= timeout:
                    return None

            except socket.error:
                return None

        return None


    def send(self, msg):
        if isinstance(msg, str):
            msg = msg.encode()

        chn_msg = [msg[idx : idx + constants.MTU] for idx in range(0, len(msg), constants.MTU)]

        for chn in chn_msg:
            self.__sock.sendto(chn, (self.__remote_ip, self.__remote_port))


    @property
    def local_ip(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)


    @property
    def local_port(self):
        return self.__sock.getsockname()[1]


    @property
    def remote_ip(self):
        return self.__remote_ip


    @property
    def remote_port(self):
        return self.__remote_port


    def close(self):
        self.__open = False
        self.__sock.close()


class container:
    pass


class daemon():

    def __init__(self, service_name):
        self.__thread = None
        self.__shared_container = container()
        self.__shared_container.sync_rx_thread = None
        self.__shared_container.sync_tx_thread = None
        self.__shared_container.enable = True
        self.__shared_container.port = None
        self.__shared_container.run = True
        self.__shared_container.master_candidate = True
        self.__shared_container.read_own_it = 0
        self.__shared_container.service_name = service_name
        self.__shared_container.mcast_listen_request = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SERVER_PORT)
        self.__shared_container.mcast_sync = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SYNC_PORT)
        self.__shared_container.sync_token = int(random.random() * 1000000) + 1


    def __del__(self):
        self.stop()


    def __readSync(shared_container):

        while shared_container.run:
            received_response, ip, port = shared_container.mcast_sync.read(constants.MCAST_SYNC_READ_TIME*2)

            if not received_response:
                return None

            elif re.match("^" + shared_container.service_name + "\\.\\d*$", received_response.decode()):
                return int(received_response.split(constants.SYNC_SEP)[1].decode())

        return None


    def __run(shared_container):

        expected_request = constants.DISCOVER_MSG_REQUEST.replace(constants.SERVICE_LABEL, shared_container.service_name).encode()
        response = constants.DISCOVER_MSG_RESPONSE.replace(constants.SERVICE_LABEL, shared_container.service_name).encode()


        while shared_container.run:
            request, ip, port = shared_container.mcast_listen_request.read()
            if not request:
                break


            request_split = request.split(constants.PORT_SEP)
            if request_split[0] == expected_request and shared_container.sync_token == 0:

                client_response = udpClient(ip, int(request_split[1]))
                if shared_container.port:
                    client_response.send(response + constants.PORT_SEP + str(shared_container.port).encode())
                else:
                    client_response.send(response)


        # Wait threads
        shared_container.sync_rx_thread.join()
        shared_container.sync_tx_thread.join()


    def __sync_tx(shared_container):

        while shared_container.run:

            time.sleep(constants.MCAST_SYNC_SEND_TIME)

            if shared_container.enable and shared_container.master_candidate:
                shared_container.mcast_sync.send(shared_container.service_name.encode() + constants.SYNC_SEP + str(shared_container.sync_token).encode())


    def __sync_rx(shared_container):


        while shared_container.run:

            sync_token = daemon.__readSync(shared_container)
            if sync_token == None:
                shared_container.master_candidate = True
                shared_container.read_own_it = 0

            elif sync_token < shared_container.sync_token:
                shared_container.master_candidate = False
                shared_container.read_own_it = 0

            elif sync_token == shared_container.sync_token:
                shared_container.read_own_it += 1

                if shared_container.read_own_it >= constants.READ_OWN_MAX_COUNT:
                    shared_container.sync_token = 0

            else:
                shared_container.read_own_it = 0


    def run(self) -> threading.Thread:
        self.__shared_container.sync_tx_thread = threading.Thread(target=daemon.__sync_tx, daemon=True, args=[self.__shared_container])
        self.__shared_container.sync_tx_thread.start()
        self.__shared_container.sync_rx_thread = threading.Thread(target=daemon.__sync_rx, daemon=True, args=[self.__shared_container])
        self.__shared_container.sync_rx_thread.start()
        self.__thread = threading.Thread(target=daemon.__run, daemon=True, args=[self.__shared_container])
        self.__thread.start()
        return self.__thread


    def stop(self):
        self.__shared_container.run = False
        self.__shared_container.mcast_listen_request.close()
        self.__shared_container.mcast_sync.close()
        if self.__thread:
            self.__thread.join()
        if self.__shared_container.sync_tx_thread:
            self.__shared_container.sync_tx_thread.join()
        if self.__shared_container.sync_rx_thread:
            self.__shared_container.sync_rx_thread.join()

    def getEnable(self):
        return self.__shared_container.enable


    def setEnable(self, enable):
        if not self.__shared_container.enable and enable:
            self.__shared_container.sync_token = int(random.random() * 1000000) + 1
        self.__shared_container.enable = enable


    def isMaster(self):
        return self.__shared_container.sync_token == 0


    def setPort(self, port:int):
        self.__shared_container.port = port


    def getPort(self) -> int:
        return self.__shared_container.port


class client():

    def __getServiceIP(self, service_name, timeout=5, retry=0) -> str:
        mcast_send_request = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SERVER_PORT)
        listen_respose = udpRandomPortListener()

        request = constants.DISCOVER_MSG_REQUEST.replace(constants.SERVICE_LABEL, service_name).encode() + constants.PORT_SEP + str(listen_respose.port).encode()
        expected_response = constants.DISCOVER_MSG_RESPONSE.replace(constants.SERVICE_LABEL, service_name).encode()

        sync_listener = mcast(constants.MCAST_DISCOVER_GRP, constants.MCAST_DISCOVER_SYNC_PORT)

        i = 0


        # Wait sync end
        start_time = float(time.time())
        while True:
            received_response, ip, port = sync_listener.read(constants.MCAST_SYNC_READ_TIME*2)

            if not received_response:
                return None, None

            elif re.match("^" + service_name + "\\.\\d*$", received_response.decode()):
                token = int(received_response.split(constants.SYNC_SEP)[1].decode())
                if token == 0:
                    break

            elif float(time.time()) - start_time > timeout:
                return None, None


        # Send request
        while retry < 0 or i <= retry:

            mcast_send_request.send(request)
            received_response, ip, port = listen_respose.read(timeout)

            if received_response:
                response_split = received_response.split(constants.PORT_SEP)

                if response_split[0] == expected_response:
                    try:
                        return ip, int(response_split[1]) if len(response_split) > 1 else None

                    except:
                        pass

            i += 1

        return None, None


    def getServiceIP(self, service_name, timeout=5, retry=0):
        ip, metadata = self.__getServiceIP(service_name, timeout, retry)
        return ip


    def getServiceIPAndPort(self, service_name, timeout=5, retry=0):
        ip, port = self.__getServiceIP(service_name, timeout, retry)
        return ip, port

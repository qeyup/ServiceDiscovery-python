#! /usr/bin/python3
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


import unittest
import ServiceDiscovery
import time
import threading
import weakref

TEST_SERVICE_NAME = "test"

class ServiceDiscover(unittest.TestCase):

    def test0_startStopDaemon(self):

        broker_discover = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        t1 = broker_discover.run()
        time.sleep(2)
        broker_discover.stop()
        time.sleep(1)
        self.assertFalse(t1.is_alive())


    def test1_deleteDaemon(self):

        def instanciate():
            broker_discover = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
            t1 = broker_discover.run()
            return weakref.ref(t1)

        weak_ptr = instanciate()
        self.assertTrue(weak_ptr() == None)


    def test2_getServiceIP(self):

        broker_discover = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover.run()
        time.sleep(2)


        test1= ServiceDiscovery.client()
        ip = test1.getServiceIP(TEST_SERVICE_NAME)
        self.assertTrue(ip != "")
        self.assertTrue(len(ip.split(".")) == 4)


    def test3_getMultipleServiceSync(self):

        broker_discover = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover.run()

        broker_discover2 = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover2.run()

        broker_discover3 = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover3.run()

        broker_discover4 = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover4.run()


        time.sleep(2)

        test1= ServiceDiscovery.client()
        ip = test1.getServiceIP(TEST_SERVICE_NAME)
        self.assertTrue(ip != None)

        ip = test1.getServiceIP(TEST_SERVICE_NAME)
        self.assertTrue(ip != None)


    def test4_getMultipleServiceSyncWithPort(self):

        broker_discover = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover.setPort(1001)
        broker_discover.run()

        broker_discover2 = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover2.setPort(1002)
        broker_discover2.run()

        broker_discover3 = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover3.setPort(1003)
        broker_discover3.run()

        broker_discover4 = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover4.setPort(1004)
        broker_discover4.run()


        time.sleep(2)

        test1= ServiceDiscovery.client()
        ip, port = test1.getServiceIPAndPort(TEST_SERVICE_NAME)
        self.assertTrue(ip != None)
        self.assertTrue(port != None)
        self.assertTrue(port > 1000)

        ip, port = test1.getServiceIPAndPort(TEST_SERVICE_NAME)
        self.assertTrue(port != None)
        self.assertTrue(port > 1000)


    def test5_multipleDaemonPreformace(self):

        daemons = []
        for i in range(50):

            broker_discover = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
            broker_discover.setPort(1000+i)
            broker_discover.run()
            daemons.append(broker_discover)


        def clientThread(results, mutex):
            client = ServiceDiscovery.client()
            ip, port = client.getServiceIPAndPort(TEST_SERVICE_NAME)
            with mutex:
                results.append(port)

        results = []
        threads = []
        save_result_mutex = threading.RLock()
        for i in range(50):
            thread = threading.Thread(target=clientThread, daemon=True, args=[results, save_result_mutex])
            thread.start()
            threads.append(thread)

        # Wait
        for thread in threads:
            thread.join()


        # Check
        resuls_clean = list(dict.fromkeys(results))
        self.assertTrue(len(resuls_clean) == 1)
        self.assertTrue(resuls_clean[0] != None)


        # Check maestry
        ok = False
        for daemon in daemons:
            if daemon.getPort() == resuls_clean[0]:
                ok = daemon.isMaster()
                break
        self.assertTrue(ok)


if __name__ == '__main__':
    unittest.main(verbosity=2)
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

TEST_SERVICE_NAME = "test"

class Test1_d2dBrokerDiscover(unittest.TestCase):

    def test1_startStopBrokerDiscover(self):
        broker_discover = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        t1 = broker_discover.run(True)
        time.sleep(2)
        broker_discover.stop()
        time.sleep(1)
        self.assertFalse(t1.is_alive())


    def test2_brokerDiscover(self):


        broker_discover = ServiceDiscovery.daemon(TEST_SERVICE_NAME)
        broker_discover.run(True)
        time.sleep(2)


        test1= ServiceDiscovery.client()
        ip = test1.getServiceIP(TEST_SERVICE_NAME)
        self.assertTrue(ip != "")
        self.assertTrue(len(ip.split(".")) == 4)


if __name__ == '__main__':
    unittest.main()
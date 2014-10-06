#!/usr/bin/env python2.7

import os
import socket
import sys
import unittest

source_dir = os.path.join(os.path.dirname(__file__), 'source')
sys.path.insert(0, source_dir)

from tests.test_notification_pusher import NotificationPusherTestCase
from tests.test_redirect_checker import RedirectCheckerTestCase
from tests.test_lib_init import LibInitCase
from tests.test_lib_utils import LibUtilsCase
from tests.test_lib_worker import LibWorkerTestCase


class MockedConnection():
    def __init__(self):
        pass

    def __enter__(self):
        self.original_connection = socket.create_connection
        socket.create_connection = self._create_connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        socket.create_connection = self.original_connection

    @staticmethod
    def _create_connection(*args, **kwargs):
        raise AssertionError('Unmocked http request')

if __name__ == '__main__':
    suite = unittest.TestSuite((
        unittest.makeSuite(NotificationPusherTestCase),
        unittest.makeSuite(RedirectCheckerTestCase),
        unittest.makeSuite(LibInitCase),
        unittest.makeSuite(LibUtilsCase),
        unittest.makeSuite(LibWorkerTestCase),
    ))

    with MockedConnection():
        result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())

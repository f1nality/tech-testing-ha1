import unittest
import gevent
import mock
import requests
from notification_pusher import notification_worker


class NotificationPusherTestCase(unittest.TestCase):
    def test_notification_worker(self):
        task = mock.Mock()
        task.task_id = 4
        task.data = {'callback_url': 'dummy_url'}

        task_queue = gevent.queue.Queue()

        response = mock.Mock()
        response.status_code = 400

        with mock.patch('requests.post', mock.Mock(return_value=response)):
            notification_worker(task, task_queue)

            assert not task_queue.empty()

            task_object = task_queue.get()

            assert task_object[0] == task
            assert 'ack' == task_object[1]

        with mock.patch('requests.post', mock.Mock(return_value=response, side_effect=requests.RequestException())):
            notification_worker(task, task_queue)

            assert not task_queue.empty()

            task_object = task_queue.get()

            assert task_object[0] == task
            assert task_object[1] == 'bury'

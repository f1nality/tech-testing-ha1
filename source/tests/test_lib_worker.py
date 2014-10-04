from unittest import TestCase
from mock import Mock, patch
from lib.worker import get_redirect_history_from_task, worker

__author__ = 'f1nal'


class WorkerTestCase(TestCase):
    def test_get_redirect_history_from_task_is_input(self):
        # TODO: incapsule
        task = Mock()
        task.task_id = 5
        task.data = {
            'url_id': '32',
            'url': 'dummy_url',
            'recheck': False
        }

        timeout = 11

        return_values = (['ERROR', 'MSG'], ['url1', 'url2'], ['counters'])

        with patch('lib.worker.get_redirect_history', Mock(return_value=return_values)):
            is_input, data = get_redirect_history_from_task(task, timeout)

            assert data['recheck']
            assert is_input

    def test_get_redirect_history_from_task_is_not_input(self):
        task = Mock()
        task.task_id = 5
        task.data = {
            'url_id': '32',
            'url': 'dummy_url',
            'recheck': False,
            'suspicious': 'asd'
        }

        timeout = 11

        return_values = (['MSG'], ['url1', 'url2'], ['counters'])

        with patch('lib.worker.get_redirect_history', Mock(return_value=return_values)):
            is_input, data = get_redirect_history_from_task(task, timeout)

            assert data['check_type'] == 'normal'
            assert not is_input

    def test_worker(self):
        config = Mock()

        config.INPUT_QUEUE_HOST = 'host'
        config.INPUT_QUEUE_PORT = '80'
        config.INPUT_QUEUE_SPACE = 1
        config.INPUT_QUEUE_TUBE = 'tube'

        config.OUTPUT_QUEUE_HOST = 'host'
        config.OUTPUT_QUEUE_PORT = 81
        config.OUTPUT_QUEUE_SPACE = 2
        config.OUTPUT_QUEUE_TUBE = 'tube'

        tube = Mock()

        tube.queue.host = 'host'
        tube.queue.port = 'port'
        tube.queue.space = 'space'
        tube.opt = {'tube': 'tube_name'}

        with patch('lib.worker.get_tube', Mock(return_value=tube)):
            worker(config, 32)

        # TODO
        pass
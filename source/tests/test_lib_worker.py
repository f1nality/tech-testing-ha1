from unittest import TestCase
from mock import Mock, patch
from lib.worker import get_redirect_history_from_task, worker

__author__ = 'f1nal'


class LibWorkerTestCase(TestCase):
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
            assert data['suspicious'] == task.data['suspicious']
            assert not is_input

    def test_get_redirect_history_from_task_is_not_input_not_suspicious(self):
        task = Mock()
        task.task_id = 5
        task.data = {
            'url_id': '32',
            'url': 'dummy_url',
            'recheck': False,
        }

        timeout = 11

        return_values = (['MSG'], ['url1', 'url2'], ['counters'])

        with patch('lib.worker.get_redirect_history', Mock(return_value=return_values)):
            is_input, data = get_redirect_history_from_task(task, timeout)

            assert data['check_type'] == 'normal'
            assert 'suspicious' not in data
            assert not is_input

    def test_worker(self):
        # TODO: incapsulate
        config = Mock()

        task = Mock()
        task_ack = Mock()

        task_meta_pri = 'fri'

        task.task_id = 55
        task.meta = Mock(return_value={
            'pri': task_meta_pri
        })
        task.ack = task_ack

        tube = Mock()
        tube_put = Mock()

        tube.opt = {'tube': 'tube_name'}
        tube.take = Mock(return_value=task)
        tube.put = tube_put

        parent_pid = 32

        is_input = True
        data = []

        with patch('lib.worker.get_tube', Mock(return_value=tube)):
            with patch('lib.worker.os.path.exists', Mock(side_effect=(
                    True, False
            ))):
                with patch('lib.worker.get_redirect_history_from_task', Mock(return_value=(is_input, data))):
                    worker(config, parent_pid)

                    tube_put.assert_called_once_with(
                        data,
                        delay=config.RECHECK_DELAY,
                        pri=task_meta_pri
                    )
                    task_ack.assert_called_once_with()

    def test_worker_is_not_input(self):
        config = Mock()

        task = Mock()
        task_ack = Mock()

        task_meta_pri = 'fri'

        task.task_id = 55
        task.meta = Mock(return_value={
            'pri': task_meta_pri
        })
        task.ack = task_ack

        tube = Mock()
        tube_put = Mock()

        tube.opt = {'tube': 'tube_name'}
        tube.take = Mock(return_value=task)
        tube.put = tube_put

        parent_pid = 32

        is_input = False
        data = []

        with patch('lib.worker.get_tube', Mock(return_value=tube)):
            with patch('lib.worker.os.path.exists', Mock(side_effect=(
                    True, False
            ))):
                with patch('lib.worker.get_redirect_history_from_task', Mock(return_value=(is_input, data))):
                    worker(config, parent_pid)

                    tube_put.assert_called_once_with(
                        data
                    )
                    task_ack.assert_called_once_with()
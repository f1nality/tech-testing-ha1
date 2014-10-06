import unittest
import mock
import requests
import tarantool
import notification_pusher
import signal
from notification_pusher import notification_worker, main_loop
from gevent import queue as gevent_queue
from mock import Mock, patch, call


class NotificationPusherTestCase(unittest.TestCase):
    def test_notification_worker_put_task(self):
        task = mock.Mock()
        task.task_id = 4
        task.data = {'callback_url': 'dummy_url'}

        task_queue = Mock()

        response = mock.Mock()

        with mock.patch('requests.post', Mock(return_value=response)):
            notification_worker(task, task_queue)

            task_queue.put.assert_called_once_with((task, 'ack'))

    def test_notification_worker_bury_task(self):
        task = mock.Mock()
        task.task_id = 4
        task.data = {'callback_url': 'dummy_url'}

        task_queue = Mock()

        response = mock.Mock()

        with mock.patch('requests.post', Mock(return_value=response, side_effect=requests.RequestException())):
            notification_worker(task, task_queue)

            task_queue.put.assert_called_once_with((task, 'bury'))

    def main_loop_done_with_processed_tasks(self, task_queue):
        notification_pusher.run_application = False

    @patch('notification_pusher.sleep', Mock())
    @patch('notification_pusher.tarantool_queue.Queue', Mock())
    def test_main_loop(self):
        pool_size = 4

        mocked_pool = Mock()
        mocked_pool.free_count = Mock(return_value=pool_size)

        mocked_done_with_processed_tasks = Mock(side_effect=self.main_loop_done_with_processed_tasks)

        mocked_worker = Mock()
        mocked_gevent_queue = Mock()

        with patch('notification_pusher.tarantool_queue.Queue', Mock()):
            with patch('notification_pusher.Pool', Mock(return_value=mocked_pool)):
                with patch('notification_pusher.done_with_processed_tasks', mocked_done_with_processed_tasks):
                    with patch('notification_pusher.Greenlet', Mock(return_value=mocked_worker)):
                        with patch('notification_pusher.gevent_queue.Queue', Mock(return_value=mocked_gevent_queue)):
                            notification_pusher.run_application = True
                            main_loop(Mock())

                            assert mocked_worker.start.call_count == pool_size
                            mocked_done_with_processed_tasks.assert_called_once_with(mocked_gevent_queue)

    @patch('notification_pusher.sleep', Mock())
    @patch('notification_pusher.tarantool_queue.Queue', Mock())
    def test_main_loop_no_task(self):
        pool_size = 4

        mocked_pool = Mock()
        mocked_pool.free_count = Mock(return_value=pool_size)

        mocked_done_with_processed_tasks = Mock(side_effect=self.main_loop_done_with_processed_tasks)

        mocked_worker = Mock()
        mocked_gevent_queue = Mock()

        mocked_task = Mock()

        mocked_tube = Mock(return_value=mocked_task)
        mocked_tube.take = Mock(return_value=None)

        mocked_tarantool_queue = Mock()
        mocked_tarantool_queue.tube = Mock(return_value=mocked_tube)

        with patch('notification_pusher.tarantool_queue.Queue', Mock(return_value=mocked_tarantool_queue)):
            with patch('notification_pusher.Pool', Mock(return_value=mocked_pool)):
                with patch('notification_pusher.done_with_processed_tasks', mocked_done_with_processed_tasks):
                    with patch('notification_pusher.Greenlet', Mock(return_value=mocked_worker)):
                        with patch('notification_pusher.gevent_queue.Queue', Mock(return_value=mocked_gevent_queue)):
                            notification_pusher.run_application = True
                            main_loop(Mock())

                            assert not mocked_worker.start.called
                            mocked_done_with_processed_tasks.assert_called_once_with(mocked_gevent_queue)

    def main_main_loop(self, config):
        notification_pusher.run_application = False

    @patch('notification_pusher.patch_all', Mock())
    @patch('notification_pusher.dictConfig', Mock())
    @patch('notification_pusher.install_signal_handlers', Mock())
    def test_main(self):
        # TODO:incapuslate
        args = Mock()
        args.daemon = True
        args.pidfile = 1
        args.config = 'config'

        mocked_config = Mock()

        mocked_daemonize = Mock()
        mocked_create_pidfile = Mock()
        mocked_load_config_from_pyfile = Mock(return_value=mocked_config)

        mocked_main_loop = Mock(side_effect=self.main_main_loop)

        with patch('notification_pusher.parse_cmd_args', Mock(return_value=args)):
            with patch('notification_pusher.daemonize', mocked_daemonize):
                with patch('notification_pusher.create_pidfile', mocked_create_pidfile):
                    with patch('notification_pusher.load_config_from_pyfile', mocked_load_config_from_pyfile):
                        with patch('notification_pusher.main_loop', mocked_main_loop):
                            notification_pusher.run_application = True
                            assert notification_pusher.main('args') == notification_pusher.exit_code

                            mocked_daemonize.assert_called_once_with()
                            mocked_create_pidfile.assert_called_once_with(args.pidfile)
                            assert mocked_load_config_from_pyfile.called
                            mocked_main_loop.assert_called_once_with(mocked_config)

    @patch('notification_pusher.patch_all', Mock())
    @patch('notification_pusher.dictConfig', Mock())
    @patch('notification_pusher.install_signal_handlers', Mock())
    def test_main_no_daemon_no_pidfile(self):
        args = Mock()
        args.daemon = False
        args.pidfile = None
        args.config = 'config'

        mocked_config = Mock()

        mocked_daemonize = Mock()
        mocked_create_pidfile = Mock()
        mocked_load_config_from_pyfile = Mock(return_value=mocked_config)

        mocked_main_loop = Mock(side_effect=self.main_main_loop)

        with patch('notification_pusher.parse_cmd_args', Mock(return_value=args)):
            with patch('notification_pusher.daemonize', mocked_daemonize):
                with patch('notification_pusher.create_pidfile', mocked_create_pidfile):
                    with patch('notification_pusher.load_config_from_pyfile', mocked_load_config_from_pyfile):
                        with patch('notification_pusher.main_loop', mocked_main_loop):
                            notification_pusher.run_application = True
                            assert notification_pusher.main('args') == notification_pusher.exit_code

                            assert not mocked_daemonize.called
                            assert not mocked_create_pidfile.called
                            assert mocked_load_config_from_pyfile.called
                            mocked_main_loop.assert_called_once_with(mocked_config)

    def main_sleep(self, seconds):
        notification_pusher.run_application = False

    @patch('notification_pusher.patch_all', Mock())
    @patch('notification_pusher.dictConfig', Mock())
    @patch('notification_pusher.install_signal_handlers', Mock())
    def test_main_main_loop_exception(self):
        args = Mock()
        args.daemon = True
        args.pidfile = 1
        args.config = 'config'

        mocked_config = Mock()

        mocked_daemonize = Mock()
        mocked_create_pidfile = Mock()
        mocked_load_config_from_pyfile = Mock(return_value=mocked_config)

        mocked_main_loop = Mock(side_effect=self.main_main_loop)

        mocked_sleep = Mock(side_effect=self.main_sleep)

        with patch('notification_pusher.parse_cmd_args', Mock(return_value=args)):
            with patch('notification_pusher.daemonize', mocked_daemonize):
                with patch('notification_pusher.create_pidfile', mocked_create_pidfile):
                    with patch('notification_pusher.load_config_from_pyfile', mocked_load_config_from_pyfile):
                        with patch('notification_pusher.main_loop', Mock(side_effect=Exception)):
                            with patch('notification_pusher.sleep', mocked_sleep):
                                notification_pusher.run_application = True
                                assert notification_pusher.main('args') == notification_pusher.exit_code

                                mocked_daemonize.assert_called_once_with()
                                mocked_create_pidfile.assert_called_once_with(args.pidfile)
                                assert mocked_load_config_from_pyfile.called
                                assert not mocked_main_loop.called

    def test_done_with_processed_tasks_execution(self):
        task = Mock()
        task_queue = Mock()

        task_queue.qsize = Mock(return_value=3)
        task_queue.get_nowait = Mock(side_effect=(
            (task, 'action1'),
            (task, 'action2'),
            gevent_queue.Empty
        ))

        notification_pusher.done_with_processed_tasks(task_queue)

        assert task.action1.called
        assert task.action2.called
        assert not task.action3.called

    def test_done_with_processed_tasks_execution_exception(self):
        task = Mock()

        task.action1 = Mock(side_effect=tarantool.DatabaseError)

        task_queue = Mock()

        task_queue.qsize = Mock(return_value=1)
        task_queue.get_nowait = Mock(side_effect=(
            (task, 'action1'),
        ))

        mocked_logger = Mock()
        original_logger = notification_pusher.logger

        notification_pusher.logger = mocked_logger
        notification_pusher.done_with_processed_tasks(task_queue)
        notification_pusher.logger = original_logger

        assert task.action1.called
        assert mocked_logger.exception.called

    def test_stop_handler_set_run_application(self):
        signum = 2

        original_run_application = notification_pusher.run_application
        notification_pusher.stop_handler(signum)

        assert not notification_pusher.run_application

        notification_pusher.run_application = original_run_application

    def test_stop_handler_set_exit_code(self):
        signum = 2

        original_exit_code = notification_pusher.exit_code
        notification_pusher.stop_handler(signum)

        assert notification_pusher.exit_code == notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum

        notification_pusher.exit_code = original_exit_code

    def test_install_signal_handlers(self):
        with patch('notification_pusher.gevent.signal', Mock()) as mocked_signal:
            notification_pusher.install_signal_handlers()

            calls = []

            for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
                calls.append(call(signum, notification_pusher.stop_handler, signum))

            mocked_signal.assert_has_calls(calls, any_order=True)
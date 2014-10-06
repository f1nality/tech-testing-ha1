import unittest
from mock import Mock, patch
from redirect_checker import main, main_loop
from lib.worker import worker
import redirect_checker


class RedirectCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self.original_logger = redirect_checker.logger
        redirect_checker.logger = Mock()

    def tearDown(self):
        redirect_checker.logger = self.original_logger

    @patch('redirect_checker.dictConfig', Mock())
    def test_main(self):
        args = Mock()
        args.daemon = True
        args.pidfile = 1
        args.config = 'config'

        mocked_config = Mock()
        mocked_config.EXIT_CODE = 44

        with patch('redirect_checker.parse_cmd_args', Mock(return_value=args)):
            with patch('redirect_checker.daemonize') as mocked_daemonize:
                with patch('redirect_checker.create_pidfile') as mocked_create_pidfile:
                    with patch('redirect_checker.load_config_from_pyfile',
                               Mock(return_value=mocked_config)) as mocked_load_config_from_pyfile:
                        with patch('redirect_checker.main_loop') as mocked_main_loop:
                            assert main('args') == mocked_config.EXIT_CODE

                            mocked_daemonize.assert_called_once_with()
                            mocked_create_pidfile.assert_called_once_with(args.pidfile)
                            assert mocked_load_config_from_pyfile.called
                            mocked_main_loop.assert_called_once_with(mocked_config)

    @patch('redirect_checker.dictConfig', Mock())
    def test_main_no_daemon_no_pidfile(self):
        args = Mock()
        args.daemon = False
        args.pidfile = None
        args.config = 'config'

        mocked_config = Mock()
        mocked_config.EXIT_CODE = 44

        with patch('redirect_checker.parse_cmd_args', Mock(return_value=args)):
            with patch('redirect_checker.daemonize') as mocked_daemonize:
                with patch('redirect_checker.create_pidfile') as mocked_create_pidfile:
                    with patch('redirect_checker.load_config_from_pyfile',
                               Mock(return_value=mocked_config)) as mocked_load_config_from_pyfile:
                        with patch('redirect_checker.main_loop') as mocked_main_loop:
                            assert main('args') == mocked_config.EXIT_CODE

                            assert not mocked_daemonize.called
                            assert not mocked_create_pidfile.called
                            assert mocked_load_config_from_pyfile.called
                            mocked_main_loop.assert_called_once_with(mocked_config)

    @patch('redirect_checker.sleep', Mock())
    @patch('redirect_checker.check_network_status', Mock(return_value=True))
    def test_main_loop(self):
        mocked_config = Mock()
        mocked_config.WORKER_POOL_SIZE = 5

        active_children = [1, 2]
        parent_pid = 5

        with patch('redirect_checker.spawn_workers') as mocked_spawn_workers:
            with patch('redirect_checker.os.getpid', Mock(return_value=parent_pid)):
                with patch('redirect_checker.active_children', Mock(side_effect=(
                        active_children, Exception
                ))):
                    try:
                        main_loop(mocked_config)
                    except Exception:
                        pass

                    mocked_spawn_workers.assert_called_with(
                        num=mocked_config.WORKER_POOL_SIZE - len(active_children),
                        target=worker,
                        args=(mocked_config,),
                        parent_pid=parent_pid
                    )

    @patch('redirect_checker.sleep', Mock())
    @patch('redirect_checker.check_network_status', Mock(return_value=True))
    def test_main_loop_no_required_workers(self):
        mocked_config = Mock()
        mocked_config.WORKER_POOL_SIZE = 5

        active_children = [1, 2, 3, 4, 5]
        parent_pid = 5

        with patch('redirect_checker.spawn_workers') as mocked_spawn_workers:
            with patch('redirect_checker.os.getpid', Mock(return_value=parent_pid)):
                with patch('redirect_checker.active_children', Mock(side_effect=(
                        active_children, Exception
                ))):
                    try:
                        main_loop(mocked_config)
                    except Exception:
                        pass

                    assert not mocked_spawn_workers.called

    @patch('redirect_checker.sleep', Mock())
    @patch('redirect_checker.check_network_status', Mock(return_value=False))
    def test_main_loop_network_offline(self):
        mocked_config = Mock()
        mocked_config.WORKER_POOL_SIZE = 5

        children1 = Mock()
        children2 = Mock()

        active_children = [children1, children2]
        parent_pid = 5

        with patch('redirect_checker.os.getpid', Mock(return_value=parent_pid)):
            with patch('redirect_checker.active_children', Mock(side_effect=(
                    active_children, Exception
            ))):
                try:
                    main_loop(mocked_config)
                except Exception:
                    pass

                for c in active_children:
                    c.terminate.assert_called_with()
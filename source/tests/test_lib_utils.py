from unittest import TestCase
from mock import patch, Mock
import mock
from lib.utils import daemonize, load_config_from_pyfile, parse_cmd_args, create_pidfile, spawn_workers, \
    check_network_status, get_tube

__author__ = 'f1nal'


class UtilsCase(TestCase):
    def test_daemonize_child_ok(self):
        with patch('os._exit', create=True) as exit_mock:
            with patch('os.fork', mock.Mock(return_value=0)):
                daemonize()

            assert not exit_mock.called

    def test_daemonize_parent_kill(self):
        with patch('os._exit', create=True) as exit_mock:
            with patch('os.fork', mock.Mock(return_value=1)):
                daemonize()

            assert exit_mock.called

    def test_daemonize_fork_exception(self):
        exception_error_number = 4
        exception_error_message = 'message'

        with patch('os.fork', mock.Mock(side_effect=OSError(exception_error_number, exception_error_message))):
            try:
                daemonize()
            except Exception as e:
                assert e.message.startswith(exception_error_message)

    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()

        with mock.patch('lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_load_config_from_pyfile_execfile_patch(self, filepath, variables):
        variables['VAR1'] = 1
        variables['VAR2'] = {'var2_1': 5}
        variables['lower_var'] = 2

    def test_load_config_from_pyfile(self):
        with patch('__builtin__.execfile', side_effect=self.test_load_config_from_pyfile_execfile_patch):
            cfg = load_config_from_pyfile('dummy.py')

            assert cfg.VAR1 == 1
            assert cfg.VAR2 == {'var2_1': 5}

            try:
                assert cfg.lower_var == 2
                self.fail('Lower attribute read loaded from pyfile')
            except AttributeError:
                pass

    def test_parse_cmd_args(self):
        config = 'config.cfg'
        pidfile = '/var/pid.file'
        parsed = parse_cmd_args(['-c', config, '-d', '-P', pidfile])

        assert parsed.config == 'config.cfg'
        assert parsed.daemon
        assert parsed.pidfile == '/var/pid.file'

    def test_spawn_workers(self):
        mocked_process = Mock()
        workers_num = 4

        with patch('lib.utils.Process', mocked_process):
            spawn_workers(workers_num, 'target', 'args', 'parent_pid')
            assert mocked_process.call_count == workers_num

    def test_check_network_status(self):
        url = 'url'
        timeout = 55

        mocked_urlopen = Mock()

        with patch('lib.utils.urllib2.urlopen', mocked_urlopen):
            assert check_network_status(url, timeout)
            mocked_urlopen.assert_called_once_with(
                url=url,
                timeout=timeout
            )

    def test_get_tube(self):
        host = 'url'
        port = 55
        space = 66
        name = 'name'

        mocked_queue = Mock()
        mocked_queue_tube = Mock()

        mocked_queue.tube = mocked_queue_tube

        with patch('lib.utils.tarantool_queue.Queue', Mock(return_value=mocked_queue)):
            get_tube(host, port, space, name)
            mocked_queue_tube.assert_called_once_with(name)
from unittest import TestCase
from mock import patch
import mock
from lib.utils import daemonize, load_config_from_pyfile, parse_cmd_args, create_pidfile

__author__ = 'f1nal'


class UtilsCase(TestCase):
    def test_daemonize(self):
        # child -> parent => not killed
        with patch('os._exit', create=True) as exit_mock:
            with patch('os.fork', mock.Mock(return_value=0)):
                daemonize()

            assert not exit_mock.called

        # parent => killed
        with patch('os._exit', create=True) as exit_mock:
            with patch('os.fork', mock.Mock(return_value=1)):
                daemonize()

            assert exit_mock.called

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
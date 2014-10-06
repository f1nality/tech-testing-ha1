import re
from unittest import TestCase
from mock import Mock, patch, call
from lib import check_for_meta, make_pycurl_request, get_url, REDIRECT_HTTP, get_redirect_history, prepare_url, \
    REDIRECT_META, fix_market_url, get_counters
import lib
from pycurl import Curl

__author__ = 'f1nal'


class LibInitCase(TestCase):
    def test_check_for_meta_ok(self):
        content = '<html><head><meta http-equiv="refresh" content="5; url=/path"></meta></head></html>'

        redirect_url = check_for_meta(content, 'http://site')

        assert redirect_url == 'http://site/path'

    def test_check_for_meta_incorrect_url(self):
        content = '<html><head><meta http-equiv="refresh" content="5; bad url"></meta></head></html>'

        redirect_url = check_for_meta(content, 'http://site')

        assert not redirect_url

    def test_check_for_meta_without_meta(self):
        content = '<html><head></head></html>'

        redirect_url = check_for_meta(content, 'http://site')

        assert not redirect_url

    def test_check_for_meta_without_content(self):
        content = '<html><head><meta></meta></head></html>'

        redirect_url = check_for_meta(content, 'http://site')

        assert not redirect_url

    def test_check_for_meta_incorrect_content(self):
        content = '<html><head><meta http-equiv="refresh" content="5; url=/path; 6"></meta></head></html>'

        redirect_url = check_for_meta(content, 'http://site')

        assert not redirect_url

    def test_make_pycurl_request_mocked_getinfo(self, info):
        if info == self.mocked_curl.REDIRECT_URL:
            return 'redirect_url'
        else:
            return info

    def test_make_pycurl_request_mocked_getinfo_none_redirect_url(self, info):
        if info == self.mocked_curl.REDIRECT_URL:
            return None
        else:
            return info

    def test_make_pycurl_request_ok(self):
        my_content = 'content'
        user_agent = 'user_agent'

        mocked_curl = Mock()
        mocked_curl.getinfo = Mock(side_effect=self.test_make_pycurl_request_mocked_getinfo)

        mocked_buff = Mock()
        mocked_buff.getvalue = Mock(return_value=my_content)

        with patch('pycurl.Curl', Mock(return_value=mocked_curl), create=True):
            with patch('lib.StringIO', Mock(return_value=mocked_buff)):
                self.mocked_curl = mocked_curl
                content, redirect_url = make_pycurl_request('url', 11, user_agent)

                assert content == my_content
                assert redirect_url == 'redirect_url'
                assert call(mocked_curl.USERAGENT, user_agent) in mocked_curl.setopt.mock_calls

    def test_make_pycurl_request_no_user_agent(self):
        my_content = 'content'
        user_agent = None

        mocked_curl = Mock()
        mocked_curl.getinfo = Mock(side_effect=self.test_make_pycurl_request_mocked_getinfo)

        mocked_buff = Mock()
        mocked_buff.getvalue = Mock(return_value=my_content)

        with patch('pycurl.Curl', Mock(return_value=mocked_curl), create=True):
            with patch('lib.StringIO', Mock(return_value=mocked_buff)):
                self.mocked_curl = mocked_curl
                content, redirect_url = make_pycurl_request('url', 11, user_agent)

                assert content == my_content
                assert redirect_url == 'redirect_url'
                assert call(mocked_curl.USERAGENT, user_agent) not in mocked_curl.setopt.mock_calls

    def test_make_pycurl_request_none_redirect_url(self):
        my_content = 'content'

        mocked_curl = Mock()
        mocked_curl.getinfo = Mock(side_effect=self.test_make_pycurl_request_mocked_getinfo_none_redirect_url)

        mocked_buff = Mock()
        mocked_buff.getvalue = Mock(return_value=my_content)

        with patch('pycurl.Curl', Mock(return_value=mocked_curl), create=True):
            with patch('lib.StringIO', Mock(return_value=mocked_buff)):
                self.mocked_curl = mocked_curl
                content, redirect_url = make_pycurl_request('url', 11)

                assert content == my_content
                assert not redirect_url

    def mocked_lib_prepare_url(self, url):
        return url

    def test_get_url(self):
        my_content = 'content'
        my_prepared_redirect_url = 'redirect_url'

        with patch('lib.make_pycurl_request', Mock(return_value=(my_content, 'redirect_url'))):
            with patch('lib.prepare_url', Mock(side_effect=self.mocked_lib_prepare_url)):
                prepared_redirect_url, redirect_type, content = get_url('url', 11, 'user_agent')

                assert prepared_redirect_url == my_prepared_redirect_url
                assert redirect_type == REDIRECT_HTTP
                assert content == my_content

    def test_get_url_market_redirect(self):
        my_content = 'content'
        market_url = 'market_url'

        with patch('lib.make_pycurl_request', Mock(return_value=(my_content, 'market://redirect_url'))):
            with patch('lib.prepare_url', Mock(side_effect=self.mocked_lib_prepare_url)):
                with patch('lib.fix_market_url', Mock(return_value=market_url)):
                    prepared_redirect_url, redirect_type, content = get_url('url', 11, 'user_agent')

                    assert prepared_redirect_url == market_url
                    assert redirect_type == REDIRECT_HTTP
                    assert content == my_content

    def test_get_url_request_exception(self):
        url = 'url'
        with patch('lib.make_pycurl_request', Mock(side_effect=ValueError)):
            prepared_redirect_url, redirect_type, content = get_url(url, 11, 'user_agent')

            assert prepared_redirect_url == url
            assert redirect_type == 'ERROR'
            assert content is None

    def test_get_url_redirect_url_none_meta_ok(self):
        my_content = 'content'
        my_prepared_redirect_url = 'redirect_url_form_meta'

        with patch('lib.make_pycurl_request', Mock(return_value=(my_content, None))):
            with patch('lib.prepare_url', Mock(side_effect=self.mocked_lib_prepare_url)):
                with patch('lib.check_for_meta', Mock(return_value='redirect_url_form_meta')):
                    prepared_redirect_url, redirect_type, content = get_url('url', 11)

                    assert prepared_redirect_url == my_prepared_redirect_url
                    assert redirect_type == REDIRECT_META
                    assert content == my_content

    def test_get_url_redirect_url_none_meta_none(self):
        my_content = 'content'
        my_prepared_redirect_url = 'redirect_url_form_meta'

        with patch('lib.make_pycurl_request', Mock(return_value=(my_content, None))):
            with patch('lib.prepare_url', Mock(side_effect=self.mocked_lib_prepare_url)):
                with patch('lib.check_for_meta', Mock(return_value=None)):
                    prepared_redirect_url, redirect_type, content = get_url('url', 11)

                    assert prepared_redirect_url == my_prepared_redirect_url
                    assert redirect_type is None
                    assert content == my_content

    def test_get_url_ok_login_redirect(self):
        my_content = 'content'
        redirect_url = 'http://www.odnoklassniki.ru/st.redirect'

        with patch('lib.make_pycurl_request', Mock(return_value=(my_content, redirect_url))):
            prepared_redirect_url, redirect_type, content = get_url('url', 11, 'user_agent')

            assert not prepared_redirect_url
            assert not redirect_type
            assert content == my_content

    def test_get_redirect_history(self):
        url = 'url'
        redirect_url = 'redirect_url'
        redirect_type = REDIRECT_HTTP
        content = 'content'

        with patch('lib.prepare_url', Mock(side_effect=self.mocked_lib_prepare_url)):
            with patch('lib.get_url', Mock(return_value=(redirect_url, redirect_type, content))):
                history_types, history_urls, counters = get_redirect_history(url, 11, max_redirects=5, user_agent='user_agent')

                assert url in history_urls and redirect_url in history_urls
                assert redirect_type in history_types
                assert counters == []

    def test_prepare_url_none(self):
        url = None
        new_url = prepare_url(None)

        assert new_url == url

    def test_fix_market_url(self):
        market_url = 'market://amarketsdm/'
        my_http_url = 'http://play.google.com/store/apps/amarketsdm/'

        http_url = fix_market_url(market_url)

        assert http_url == my_http_url

    def test_get_counters(self):
        lib.COUNTER_TYPES = (
            ('GOOGLE_ANALYTICS', re.compile(r'.*google-analytics\.com/ga\.js.*', re.I+re.S)),
            ('YA_METRICA', re.compile(r'.*mc\.yandex\.ru/metrika/watch\.js.*', re.I+re.S)),
        )

        counters = get_counters('mc.yandex.ru/metrika/watch.js')

        assert 'YA_METRICA' in counters
        assert 'GOOGLE_ANALYTICS' not in counters
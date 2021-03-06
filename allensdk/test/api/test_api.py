# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the
# Allen Institute's written permission.
# For purposes of this license, commercial purposes is the incorporation of the
# Allen Institute's software into anything for which you will charge fees or
# other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import pytest
from mock import MagicMock, patch, mock_open
from allensdk.api.api import Api
import allensdk.core.json_utilities as ju
from requests.exceptions import HTTPError
from six.moves import builtins
import requests


@pytest.fixture
def api():
    ju.read_url_post = \
        MagicMock(name='read_url_post',
                  return_value={'whatever': True})

    api = Api()

    return api


@pytest.mark.xfail
def test_failed_download(api):
    with pytest.raises(HTTPError) as e_info:
        api.retrieve_file_over_http('http://example.com/yo.jpg',
                                    '/tmp/testfile')

        assert e_info.typename == 'HTTPError'


def test_request_timeout(api):
    def raise_read_timeout(response, path=None):
        raise requests.exceptions.ReadTimeout

    with patch('requests.get', return_value=MagicMock()) as get_mock:
        response_mock = get_mock.return_value
        response_mock.raise_for_status = MagicMock()
        
        with patch(
            'requests_toolbelt.downloadutils.stream.stream_response_to_file',
            MagicMock(name='stream_response_to_file',
                      side_effect=raise_read_timeout)) as stream_mock:
            with patch(builtins.__name__ + '.open',
                       mock_open(),
                       create=True) as open_mock:
                with patch('os.remove', MagicMock()) as os_remove:
                    with pytest.raises(requests.exceptions.ReadTimeout) as e_info:
                        api.retrieve_file_over_http('http://example.com/yo.jpg',
                                                    '/tmp/testfile')

    assert e_info.typename == 'ReadTimeout'
    stream_mock.assert_called_with(response_mock, path=open_mock.return_value)
    get_mock.assert_called_once_with('http://example.com/yo.jpg',
                                     stream=True,
                                     timeout=(9.05, 31.1))
    open_mock.assert_called_once_with('/tmp/testfile', 'wb')
    os_remove.assert_called_once_with('/tmp/testfile')


def test_do_query_post(api):
    api.do_query(lambda *a, **k: 'http://localhost/%s' % (a[0]),
                 lambda d: d,
                 "wow",
                 post=True)

    ju.read_url_post.assert_called_once_with('http://localhost/wow')


def test_do_query_get(api):
    ju.read_url_get = \
        MagicMock(name='read_url_get',
                  return_value={'whatever': True})

    api.do_query(lambda *a, **k: 'http://localhost/%s' % (a[0]),
                 lambda d: d,
                 "wow",
                 post=False)

    ju.read_url_get.assert_called_once_with('http://localhost/wow')


def test_load_api_schema(api):
    ju.read_url_get = \
        MagicMock(name='read_url_get',
                  return_value={'whatever': True})

    api.load_api_schema()

    ju.read_url_get.assert_called_once_with(
        'http://api.brain-map.org/api/v2/data/enumerate.json')

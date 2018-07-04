from multidict import CIMultiDict
from vcr.errors import UnhandledHTTPRequestError
from vcr.matchers import method, query, uri, raw_body
from yarl import URL
from aiohttp import ClientResponse, StreamReader
from aiohttp.helpers import TimerNoop
from unittest.mock import Mock
import functools

import collections
import os.path
import vcr

default_library = os.path.join(os.path.dirname(__file__), 'cassettes/')


class CassetteStore(object):

    def __init__(self, cassette_library_dir=None, ignore_hosts=(),
                 ignore_localhost=False, record_mode='once'):
        self._library_dir = None
        self._cassette = None

        self.library_dir = cassette_library_dir
        self.record_mode = record_mode

        # Default ignore
        self.ignore = set()

        # Add other ignored hosts
        if ignore_localhost:
            self.add_ignored_host({'localhost', '127.0.0.1'})

        if ignore_hosts:
            self.add_ignored_host(set(ignore_hosts))

    def add_ignored_host(self, host):
        if type(host) != set:
            host = {host}
        self.ignore.update(host)

    @property
    def library_dir(self):
        return self._library_dir or default_library

    @library_dir.setter
    def library_dir(self, library_dir):
        self._library_dir = library_dir

    @functools.lru_cache(maxsize=3)
    def load_cassette(self, url):
        # Per-host cassettes unless self._cassette is specified
        name = self._cassette or URL(url).host
        path = os.path.join(self.library_dir, name)
        cassette = vcr.cassette.Cassette(path, match_on=(uri, method, query, raw_body))
        cassette._load()
        return cassette

    def use_cassette(self, cassette=None):
        self._cassette = cassette

    def skip(self, url):
        for ignore in self.ignore:
            if ignore in url:
                return True
        return False

    async def store_response(self, method, url, params, data, headers,
                             response):
        """This function is called for when we want to add a new record in the cassette
        """
        if type(url) == URL:
            url = url.human_repr()

        # Only store those we don't skip
        if not self.skip(url):
            # Create the request object
            if not data:
                data = {}
            if params:
                data.update(params)

            request = vcr.request.Request(method, url, data, headers)

            data_type = 'binary'
            resp_data = await response.read()

            # Create the vcr response as it will be stored
            vcr_response = {
                'status': {
                    'code': response.status,
                    'message': response.reason,
                },
                'headers': dict(response.headers),
                'body': {
                    'data': (resp_data),
                    'type': data_type
                },
                'url': response.url.human_repr(),
            }

            # Store it and save
            cassette = self.load_cassette(url)
            cassette.append(request, vcr_response)
            cassette._save(force=True)

    def build_response(self, method, url, params, data, headers):
        """"""
        try:
            if type(url) == URL:
                url = url.human_repr()

            # Check if we have to skip it
            if self.skip(url):
                return None

            # Go check see if response is in cassette
            if not data:
                data = {}
            if params:
                data.update(params)

            request = vcr.request.Request(method, url, data, headers)
            cassette = self.load_cassette(url)
            resp_json = cassette.play_response(request)
        except UnhandledHTTPRequestError:
            # Response not seen yet in cassette
            return None

        # Response was found in cassette
        cassette.play_counts = collections.Counter()
        # Create the response
        resp = ClientResponse(method,
                              URL(url),
                              request_info=Mock(),
                              writer=Mock(),
                              continue100=None,
                              timer=TimerNoop(),
                              traces=[],
                              loop=Mock(),
                              session=Mock(),
                              auto_decompress=False)

        # Replicate status code and reason
        resp.status = resp_json['status']['code']

        # Set default plain/text if no Content-Type
        try:
            resp_json['headers']['Content-Type']
        except KeyError:
            resp_json['headers']['Content-Type'] = 'plain/text'

        # Set headers and content
        resp.headers = CIMultiDict(resp_json['headers'])
        resp.content = StreamReader(Mock())

        # Get the data
        data = resp_json['body']['data']

        resp.content.feed_data(data)
        resp.content.feed_eof()

        return resp

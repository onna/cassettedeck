from multidict import CIMultiDict
from vcr.errors import UnhandledHTTPRequestError
from vcr.matchers import method, query, uri, raw_body
from yarl import URL
from aiohttp import ClientResponse, StreamReader
from aiohttp.helpers import TimerNoop
from unittest.mock import Mock
import collections
import copy
import os.path
import vcr

default_library = os.path.join(os.path.dirname(__file__), 'cassettes/')


class CassetteStore(object):
    """This class wraps all logic related to cassettes, such as storing
    new requests, building the replayed response, etc.
    """
    def __init__(self, cassette_library_dir=None, ignore_hosts=(),
                 ignore_localhost=False, record_mode='once',
                 custom_matchers=None):
        self._library_dir = None
        self._cassette = None
        self._cassette_cache = {}
        self.library_dir = cassette_library_dir
        self.record_mode = record_mode
        self.custom_matchers = custom_matchers or []

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

    @property
    def match_on(self):
        default = (uri, method, query, raw_body)
        if not self.custom_matchers:
            return default
        is_list = isinstance(self.custom_matchers, list)
        is_tuple = isinstance(self.custom_matchers, tuple)
        is_iterable = is_list or is_tuple
        if not is_iterable:
            return (self.custom_matchers, )
        return self.custom_matchers

    def load_cassette(self, url):
        # Per-host cassettes unless self._cassette is specified
        name = self._cassette or URL(url).host
        path = os.path.join(self.library_dir, name)

        if path not in self._cassette_cache:
            cassette = vcr.cassette.Cassette(path, match_on=self.match_on)
            cassette._load()
            self._cassette_cache[path] = cassette

        return self._cassette_cache[path]

    def store_cassette(self, cassette):
        cassette._save(force=True)
        # Update cache
        self._cassette_cache[cassette._path] = cassette

    def use_cassette(self, cassette=None):
        self._cassette = cassette

    def skip(self, url):
        for ignore in self.ignore:
            if ignore in url:
                return True
        return False

    async def store_response(self, method, url, params0, data0, headers0,
                             response):
        """This function is called for when we want to add a new record in the cassette
        """
        params = copy.deepcopy(params0)
        data = copy.deepcopy(data0)
        headers = copy.deepcopy(headers0)

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
            self.store_cassette(cassette)

            return vcr_response

    def build_response(self, method, url, params, data, headers):
        """"""
        try:
            if type(url) == URL:
                url = url.human_repr()

            # Check if we have to skip it
            if self.skip(url):
                return None, True

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
            return None, False

        # Response was found in cassette
        cassette.play_counts = collections.Counter()
        # Create the response
        resp = ClientResponse(
            method,
            URL(url),
            request_info=Mock(),
            writer=Mock(),
            continue100=None,
            timer=TimerNoop(),
            traces=[],
            loop=Mock(),
            session=Mock(),
        )
        # Replicate status code and reason
        resp.status = resp_json['status']['code']
        resp.reason = resp_json['status']['message']

        # Set headers and content
        resp._headers = CIMultiDict(resp_json['headers'])
        resp.content = StreamReader(Mock())

        # Get the data
        data = resp_json['body']['data']

        resp.content.feed_data(data)
        resp.content.feed_eof()

        return resp, False

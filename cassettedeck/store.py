from multidict import CIMultiDict
from vcr.errors import UnhandledHTTPRequestError
from vcr.matchers import method
from vcr.matchers import query
from vcr.matchers import uri
from yarl import URL

import collections
import os.path
import vcr

rabbitmq_endpoint = "http://rabbitmq-front.rabbitmq.svc.cluster.local:8081/"  # noqa
messaging_url = 'http://api.userapi.svc.cluster.local:6543/messaging'  # noqa
oauth_server = 'http://localhost:6543/oauth/'

default_library = os.path.join(os.path.dirname(__file__), 'cassettes/')


class CassetteStore(object):
    def __init__(self, cassette=None, ignored=None):
        self._cassette = cassette
        # Default ignore
        self.ignore = {
            'localhost',
            '127.0.0.1',
            URL(oauth_server).host,
            URL(messaging_url).host,
            URL(rabbitmq_endpoint).host
        }
        # Add other ignored hosts
        if ignored:
            self.add_ignored_host(ignored)
        # Cassettes folder
        self.library_dir = default_library

    def add_ignored_host(self, host):
        if type(host) != set:
            host = {host}
        self.ignore.update(host)

    def set_library_dir(self, library_dir):
        if library_dir:
            self.library_dir = library_dir

    def load_cassette(self, url):
        # Per-host cassettes unless self._cassette is specified
        name = self._cassette or URL(url).host
        path = os.path.join(self.library_dir, name)
        cassette = vcr.cassette.Cassette(path, match_on=(uri, method, query))
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
            request = vcr.request.Request(method, url, data, headers)

            # Check if it's text
            try:
                data = await response.text()
                data_type = 'text'
            # Try with reading as a binary
            except UnicodeDecodeError:
                data = await response.read()
                data_type = 'binary'

            # Create the vcr response as it will be stored
            vcr_response = {
                'status': {
                    'code': response.status,
                    'message': response.reason,
                },
                'headers': dict(response.headers),
                'body': {
                    'data': (data),
                    'type': data_type
                },
                'url': response.url,
            }
            # Store it and save
            cassette = self.load_cassette(url)
            cassette.append(request, vcr_response)
            cassette._save()

    def build_response(self, method, url, params, data, headers):
        """"""
        try:
            if type(url) == URL:
                url = url.human_repr()

            # Check if we have to skip it
            if self.skip(url):
                return None

            # Go check see if response is in cassette
            request = vcr.request.Request(method, url, data, headers)
            cassette = self.load_cassette(url)
            resp_json = cassette.play_response(request)
        except UnhandledHTTPRequestError:
            # Response not seen yet in cassette
            return None

        # Response was found in cassette
        cassette.play_counts = collections.Counter()
        # Create the response
        resp = ClientResponse(method, URL(url))

        # Replicate status code and reason
        resp.status = resp_json['status']['code']

        # Get the data
        data = resp_json['body']['data']
        data_type = resp_json['body']['type']

        # Set default plain/text if no Content-Type
        try:
            resp_json['headers']['Content-Type']
        except KeyError:
            resp_json['headers']['Content-Type'] = 'plain/text'

        # Set headers and content
        resp.headers = CIMultiDict(resp_json['headers'])
        resp.content = StreamReader()
        if isinstance(data, str):
            data = data.encode('utf8')
        resp.content.feed_data(data)
        resp.content.feed_eof()
        # Return recorded response
        return resp

# Declare the singleton
cassetteStore = CassetteStore()

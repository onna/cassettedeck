import pytest
import os
from cassettedeck.service import BaseService
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
from multiprocessing import Process

from cassettedeck.deck import CassetteDeck


@pytest.fixture(scope='function')
def ctd():
    yield CassetteDeck(
        mocked_services=[
            MockedService(),
        ],
    )


@pytest.fixture(scope='function')
def local_server():
    # Start echo server
    server = HTTPServer(('', 8080), BaseHTTPRequestHandler)
    p = Process(target=server.serve_forever)
    p.start()
    yield
    p.terminate()


@pytest.fixture(scope='function')
def ctd_ignore_localhost(local_server):
    # Yield cassettedeck
    yield CassetteDeck(
        ignore_localhost=True,
    )


class MockedService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.server = 'http://mocked.service.com'
        self.treasure = 'foo'

    def matches(self, url):
        return url.startswith(self.server)

    async def get_the_treasure(self, params=None, data=None, headers={}):
        return 200, self.treasure, 'text/plain'


@pytest.fixture(scope='function')
def ctd_custom_dir():
    cassettes_folder = os.path.join(os.path.curdir, f'stored_requests')
    yield CassetteDeck(cassette_library_dir=cassettes_folder)

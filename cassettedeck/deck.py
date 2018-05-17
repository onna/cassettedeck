import aiohttp
import functools
import logging
from contextlib import contextmanager
from cassettedeck.store import CassetteStore


class CassetteDeck:
    """"""

    def __init__(self, cassette_library_dir=None, ignore_localhost=False,
                 ignore_hosts=()):
        self.cassette_store = CassetteStore(cassette_library_dir=cassette_library_dir,  # noqa
                                            ignore_localhost=ignore_localhost,
                                            ignore_hosts=ignore_hosts)

    @contextmanager
    def use_cassette(self, cassette):
        with self:
            self.cassette_store.use_cassette(cassette)
            yield self
            self.cassette_store.use_cassette(None)

    def __enter__(self):
        # We put the original _request method in a new method _original_request
        aiohttp.client.ClientSession._original_request = \
            aiohttp.client.ClientSession._request
        # We replace the _request for our own request handler function
        aiohttp.client.ClientSession._request = functools.partialmethod(
            handle_request,
            _cassette_store=self.cassette_store
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We set it back to the original function
        aiohttp.client.ClientSession._request = \
            aiohttp.client.ClientSession._original_request


async def handle_request(self, method: str, url: str, params=None, data=None,
                         headers=None, _cassette_store=None, *args, **kwargs):
    """Return mocked response object or raise connection error."""
    # Attempt to build response from stored cassette
    resp = _cassette_store.build_response(method, url, params, data, headers)

    if not resp:
        # Call original request if cassette wasn't there
        resp = await self._original_request(method, url,
                                            params=params, data=data,
                                            headers=headers, *args,
                                            **kwargs)
        # Store cassette
        await _cassette_store.store_response(method, url, params, data,
                                             headers, resp)
        logging.info(f"Recording [{method}] {url}")
    else:
        logging.info(f"Loading from cassette [{method}] {url}")

    return resp

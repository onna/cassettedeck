import aiohttp
import functools
import asyncio
import logging
from contextlib import contextmanager
from cassettedeck.store import CassetteStore


class CassetteDeck:
    """This is the object to use as a fixture in tests.
    """

    def __init__(self, cassette_library_dir=None, ignore_localhost=False,
                 ignore_hosts=(), mode='once', mocked_services=None):
        self.cassette_store = CassetteStore(cassette_library_dir=cassette_library_dir,  # noqa
                                            ignore_localhost=ignore_localhost,
                                            ignore_hosts=ignore_hosts,
                                            record_mode=mode)
        self.mocked_services = mocked_services

    @contextmanager
    def use_cassette(self, cassette, mode='once', custom_matchers=None):
        with self:
            previous_custom_matchers = self.cassette_store.custom_matchers
            if custom_matchers:
                self.cassette_store.custom_matchers = custom_matchers
            self.cassette_store.use_cassette(cassette)
            yield self
            # Restore state
            self.cassette_store.custom_matchers = previous_custom_matchers
            self.cassette_store.use_cassette(None)

    def __enter__(self):
        if not hasattr(aiohttp.client.ClientSession, '_original_request'):
            # We put the original _request method in a new method _original_request
            aiohttp.client.ClientSession._original_request = \
                aiohttp.client.ClientSession._request

        # We replace the _request for our own request handler function
        aiohttp.client.ClientSession._request = functools.partialmethod(
            handle_request,
            _cassette_store=self.cassette_store,
            _mocked_services=self.mocked_services,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We set it back to the original function
        aiohttp.client.ClientSession._request = \
            aiohttp.client.ClientSession._original_request


async def handle_request(self, method: str, url: str, params=None,
                         data=None, headers=None,
                         _cassette_store=None, _mocked_services=None,
                         *args, **kwargs):
    """Return mocked response object or raise connection error."""

    # Check if url belongs to a mocked service
    for service in _mocked_services or []:
        if service.matches(str(url)):
            return await service.build_response(
                self, method, url, params=params, data=data,
                headers=headers, *args, **kwargs)

    # Attempt to build response from stored cassette
    resp, skip = _cassette_store.build_response(method, url, params, data, headers)

    if not resp:
        # Call original request if cassette wasn't there
        resp = await self._original_request(method, url,
                                            params=params, data=data,
                                            headers=headers, *args,
                                            **kwargs)
        if skip:
            # Return original response, do not store the response
            return resp

        # Store cassette
        stored = await _cassette_store.store_response(method, url, params, data,
                                                      headers, resp)

        # Refill the buffer
        if resp.content.is_eof():
            content = asyncio.StreamReader()
            content.feed_data(stored['body']['data'])
            content.feed_eof()
            resp.content = content
        logging.info(f"Recording [{method}] {url}")
    else:
        logging.info(f"Loading from cassette [{method}] {url}")

    return resp

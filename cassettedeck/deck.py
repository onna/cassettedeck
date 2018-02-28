import aiohttp
import vcr

from cassettedeck.store import cassetteStore


class CassetteDeck:
    """"""
    def __enter__(self):
        # We put the original _request method in a new method _original_request
        aiohttp.client.ClientSession._original_request = aiohttp.client.ClientSession._request
        # We replace the _request for our own request handler function
        aiohttp.client.ClientSession._request = handle_request

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We set it back to the original function
        aiohttp.client.ClientSession._request = aiohttp.client.ClientSession._original_request


async def handle_request(self, method: str, url: str, params=None,
                         data=None, headers=None, *args, **kwargs):
    """Return mocked response object or raise connection error."""
    # Attempt to build response from stored cassette
    resp = cassetteStore.build_response(method, url, params, data, headers)

    if not resp:
        # Call original request if cassette wasn't there
        resp = await self._original_request(method, url,
                                            params=params, data=data,
                                            headers=headers, *args,
                                            **kwargs)
        # Store cassette
        await cassetteStore.store_response(method, url, params, data,
                                      headers, resp)
    return resp

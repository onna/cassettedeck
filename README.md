# CassetteDeck

This package provides a tool for replying HTTP traffic. It is similar
to `vcrpy` -- we actually still depend on it -- but with just the
functionality we need.

## How it works

Essentially, the `CassetteDeck` class provides a context manager to be
used in a pytest fixture, which can be included in all tests for which
we want requests to be stored and replayed thereafter.

When entering this context manager, the
`aiohttp.ClientSession._request` is replace by our own
`handle_request` function. What we do is to try to build the response
from the cassette (there is a per-host cassette, unless a particular
cassette is specified with `use_cassette`). If no stored response was
found, we perform the original aiohttp request and store the response
in the cassette. Therefore, next time the same request appears, it
will be replayed.

## Ignored hosts

With `CassetteDeck` we can also specify that we don't want requests to
localhost to be recorded with the `ignore_localhost=True` parameter.

Moreover, the `ignored_hosts` list parameter can be used to extend the
ignored servers. Those will always return the actual server request.

## Mocked services

`CassetteDeck` allows us to specify a list of mocked services for
which matching requests will be translated into function calls in the
mock object.

An example would be:

``` python

class MockedService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.server = 'http://mocked.service.com'
        self.treasure = 'foo'

    def matches(self, url):
        return url.startswith(self.server)

    async def get_the_treasure(self, params=None, data=None, headers={}):
        return 200, self.treasure, 'text/plain'
```

A mocked service must inherit from `BaseService` and re-implement the
`matches` method. In this case, a request to
`http://mocked.service.com/get_the_treasure` will be routed to the
`get_the_treasure` method, thus returning whatever we want in the
mock.


## Custom matchers

By default, `CassetteDeck` serializes both the request and the
response inside the cassette. Let's assume a request r1 produces a
certain response that is stored. When a new request r2 comes, it will
replay with a stored response if r2 matches one of the stored requests
in the cassette.

The default matcher checks that the method, url, query parameters, raw
body are the same.

However, `CassetteDeck` supports specifying custom matchers for
certain tests with the `custom_matchers` argument. This way, one can
implement non-standard logic to match requests, for instance, using
specific parameters on the headers.


An example would be:

``` python

def CustomMatcher(r1, r2):
    """This matcher will return the same response for all requests that
    have 'hello' in the request body.
    """
    if 'hello' not in r1.body.decode():
        return False

    if 'hello' not in r2.body.decode():
        return False
    return True
```

Thus can be specified in the `custom_matchers` list along with other
matchers:

``` python

from cassettedeck import CassetteDeck
from vcr.matchers import uri
from vcr.matchers import method

ctd = CassetteDeck()
with ctd.use_cassette(
    'my_cassette',
    custom_matchers=[
        CustomMatcher,
        uri,
        method,
    ])
```

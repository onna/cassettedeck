Changelog
=========
3.0.0
-----

- Make it compatible with aiohttp > 3.6

2.2.0
-----

- Update dependencies 

2.1.2
-----

- Fix flake8 error

2.1.1
-----

- Add required parameter to streamreader

2.1.0
-----

- add generic VCR function to help with test implementation

2.0.3
-----

- relax several requirements
- add a simple makefile

2.0.2
-----

- Pin aiohttp to >=3.4 <3.6
- Solve flake8 warnings

2.0.1
------

- remove content-type injection in stored data

2.0.0
-----

- Upgraded to aiohttp >= 3.4.4 [lferran]

1.1.12
------

- Support custom matches [lferran]

1.1.11
------

- Support mocked services [lferran]

1.1.10
------

- Bugfix: return original response for ignored hosts [lferran]

1.1.9
-----

 - Fix load_cassette() cache

1.1.8
-----

 - Fill the reason field in the response

1.1.7
-----

 - When consuming the response content and serializing the returned response was at EOF.
   Refill the buffer so it can be consumed again.

1.1.6
-----

 - Problem with some method that has side effects everywhere!

1.1.5
-----

 - Problem serializing the request body

1.1.4
-----

 - Query response using params too
 - Cache the cassette so we dont need to deserialize for every request

1.1.3
-----

 - Allow different modes (all, once)
 - Problem serializing URL

1.1.2
-----

 - Fixed loading cassettes with request matching the 'uri', 'method' and 'query' but not matching the 'body'


1.1.1
-----

 - Fixed a recursion bug when nesting `CassetteDeck` contexts


1.1.0
-----

 - Changed Cassettedeck API to make it more like vcrpy
 - Only compatible with aiohttp~=3.1.0
 - Storing all cassettes as binary to fix text encoding errors during serialization/deserialization
 - Added some pytests based on `test.py`


1.0.0
-----

 - Initial commit [@lferran]

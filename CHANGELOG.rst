Changelog
=========

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

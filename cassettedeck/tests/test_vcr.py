import os

import aiohttp
from aiounittest import AsyncTestCase

from cassettedeck.vcr import vcr


class TestVCR(AsyncTestCase):

    async def test_should_store_cassette_at_expected_location(self):
        expected_path = os.path.join(os.path.dirname(__file__), "cassettes", f"{self.id()}.yaml")
        self.assertFalse(os.path.exists(expected_path))

        with vcr(self):
            async with aiohttp.request("GET", "https://example.com") as response:
                response.raise_for_status()

        self.assertTrue(os.path.isfile(expected_path))
        os.remove(expected_path)

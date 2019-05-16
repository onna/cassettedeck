import pytest
import aiohttp
import os


pytestmark = pytest.mark.asyncio


async def download_text():
    url = 'http://www.marca.com'
    return await download(url, data_type='text')


async def download_image():
    url = 'https://www.edominations.com/public/upload/newspaper/462.jpg'
    return await download(url, data_type='binary')


async def echo_post(data):
    url = 'https://postman-echo.com/post'
    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, data=data) as resp:
            return await resp.text()


async def calling_localhost():
    url = 'http://localhost:8080/foo/bar'
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            return await resp.text()


async def calling_mocked_service(path):
    url = os.path.join('http://mocked.service.com', path)
    async with aiohttp.ClientSession() as s, s.get(url) as resp:
        assert resp.status == 200
        assert resp.headers.get('Content-Type') == 'text/plain'
        result = await resp.text()
        return result


async def download(url, data_type):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            if str(resp.status).startswith('2'):
                if data_type == 'text':
                    data = await resp.text()
                elif data_type == 'binary':
                    data = await resp.read()
                else:
                    raise ValueError()
                return data
            else:
                text = await resp.text()
                msg = f'{resp.status} -- {resp.reason} -- {text}'
                raise Exception(f"Errors fetching {url} | {msg}")


async def test_simple(ctd):
    with ctd:
        original = await download_image()
        cassette = await download_image()
        assert isinstance(original, bytes)
        assert isinstance(cassette, bytes)
        assert original == cassette

        original = await download_text()
        cassette = await download_text()
        assert isinstance(original, str)
        assert isinstance(cassette, str)
        assert original == cassette


async def test_use_cassete(ctd):
    with ctd.use_cassette('test_cassette_1'):
        original = await download_image()
        cassette = await download_image()
        assert isinstance(original, bytes)
        assert isinstance(cassette, bytes)
        assert original == cassette

        original = await download_text()
        cassette = await download_text()
        assert isinstance(original, str)
        assert isinstance(cassette, str)
        assert original == cassette


async def test_use_cassete_lib_dir(ctd_custom_dir):
    with ctd_custom_dir.use_cassette('test_cassette_2'):
        original = await download_image()
        cassette = await download_image()
        assert isinstance(original, bytes)
        assert isinstance(cassette, bytes)
        assert original == cassette

        original = await download_text()
        cassette = await download_text()
        assert isinstance(original, str)
        assert isinstance(cassette, str)
        assert original == cassette


async def test_use_cassete_cache(ctd):
    with ctd.use_cassette('test_cassette_cache'):
        req1 = await echo_post('hello')
        req2 = await echo_post('world')
        assert req1 != req2
        assert isinstance(req1, str)
        assert isinstance(req2, str)

        # Trying again. We should get both values from the cache
        req1 = await echo_post('hello')
        req2 = await echo_post('world')
        assert req1 != req2
        assert isinstance(req1, str)
        assert isinstance(req2, str)


async def test_ingore_localhost_works(ctd_ignore_localhost):
    with ctd_ignore_localhost.use_cassette('localhost_ignored'):
        await calling_localhost()

        # Check that request was not stored in cassette
        assert not ctd_ignore_localhost.cassette_store._cassette_cache
        try:
            library_dir = ctd_ignore_localhost.cassette_store.library_dir
            cassette = ctd_ignore_localhost.cassette_store._cassette
            with open(os.path.join(library_dir, cassette), 'r') as f:
                ep = f.read()
                # If cassette file exists, localhost should not be
                # present!
                assert 'localhost' not in ep
        except Exception as e:
            # Cassette file does not exist
            assert isinstance(e, FileNotFoundError)

        # Not ignored hosts should be recorded
        await echo_post('hello')
        assert ctd_ignore_localhost.cassette_store._cassette_cache
        with open(os.path.join(library_dir, cassette), 'r') as f:
            ep = f.read()
            assert 'postman-echo.com' in ep


async def test_mocked_services_work(ctd):
    with ctd.use_cassette('test_mocked_services'):
        result = await calling_mocked_service('get_the_treasure')
        assert result == 'foo'


def CustomMatcher(r1, r2):
    """This matcher will return the same response for all requests that
    have 'hello' in the request body.
    """
    if 'hello' not in r1.body.decode():
        return False

    if 'hello' not in r2.body.decode():
        return False
    return True


async def test_custom_matcher(ctd):
    with ctd.use_cassette('test_custom_matcher',
                          custom_matchers=[CustomMatcher]):
        # Get the cassette
        cassette = ctd.cassette_store.load_cassette('test_custom_matcher')
        await echo_post('hello-my-friend')
        await echo_post('byebye-my-friend')
        await echo_post('adeu')
        before = len(cassette.data)
        # The number of stored responses should be the same as before,
        # because the last request did not result in a new
        # stored response
        await echo_post('yes-yes-hello')
        assert len(cassette.data) == before

import aiohttp
import asyncio
import os
import shutil

from cassettedeck.deck import CassetteDeck


async def download_text():
    url = 'http://www.marca.com'
    return await download(url, data_type='text')

async def download_image():
    url = 'https://www.edominations.com/public/upload/newspaper/462.jpg'
    return await download(url, data_type='binary')

async def download(url, data_type=None):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            if str(resp.status).startswith('2'):
                print(f"Correctly fetched {url}")
                if not data_type or data_type == 'text':
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

async def test_image():
    # Get it first -- this will create a cassette
    original = await download_image()
    cassette = await download_image()
    assert isinstance(original, bytes)
    assert isinstance(cassette, bytes)
    assert original == cassette
    # Write binary into file
    with open('image.jpg', 'wb') as f:
        f.write(cassette)

async def test_text():
    # Get it first -- this will create a cassette
    original = await download_text()
    cassette = await download_text()
    assert isinstance(original, str)
    assert isinstance(cassette, str)
    # It happens that are not equal becuse we are encoding with the
    # wrong on storing it wronge format
    assert original != cassette

def delete_cassettes():
    folder = os.path.join(os.path.curdir, f'cassettedeck/cassettes/')
    try:
        shutil.rmtree(folder)
    except FileNotFoundError:
        pass

async def main():
    with CassetteDeck() as ctd:
        delete_cassettes()
        await test_image()
        await test_text()

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(
        main()
    )

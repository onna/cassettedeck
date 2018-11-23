from aiohttp import ClientResponse
from aiohttp import StreamReader
from multidict import CIMultiDict
from yarl import URL
from aiohttp import hdrs
from aiohttp.helpers import TimerNoop
from unittest.mock import Mock
import json
import asyncio


class BaseService:
    def __init__(self):
        self.clear()

    def clear(self):
        self.requests = []
        self.responses = []

    async def build_response(self, session, method, url,
                             params=None, data=None,
                             headers=None, *args, **kwargs):
        self.requests.append({
            'method': method,
            'url': url,
            'params': params,
            'data': data,
            'headers': headers
        })
        url = URL(url)
        url_parts = [p.split('?')[-1] for p in url.parts]

        if data is None and 'json' in kwargs:
            data = json.dumps(kwargs['json'])
        resp = ClientResponse(
            method,
            url,
            request_info=Mock(),
            writer=Mock(),
            continue100=None,
            timer=TimerNoop(),
            traces=[],
            loop=Mock(),
            session=Mock(),
        )
        func_name = '_'.join(url_parts[-2:])
        func = None
        if hasattr(self, func_name):
            func = getattr(self, func_name)
        else:
            func_name = url_parts[-1]
            if hasattr(self, func_name):
                func = getattr(self, func_name)

        if func is not None:
            status, data, ct = await func(params or url.query, data, headers)
            resp.status = status
        else:
            print(f'Method {func_name} not implemented')
            resp.status = 200
            if method.lower() == 'patch':
                resp.status = 204
            ct = 'application/json'
            data = '{}'

        resp._headers = CIMultiDict({hdrs.CONTENT_TYPE: ct})
        loop = asyncio.get_event_loop()
        protocol = Mock(_reading_paused=False)
        resp.content = StreamReader(protocol, loop=loop)
        if isinstance(data, str):
            data = data.encode('utf8')
        resp.content.feed_data(data)
        resp.content.feed_eof()
        self.responses.append(resp)
        return resp

    def matches(self, url):
        raise NotImplementedError()

import aiohttp
import asyncio
from xml.etree.ElementTree import fromstring
import json

"""
http://feeds.rasset.ie/rteavgen/search/?type=mobile-radio&query=an%20taobh<
"""


class Episode():
    EP_URI = 'http://feeds.rasset.ie/rteavgen/playlist/'

    @classmethod
    def from_id(cls, ep_id):
        resp = yield from aiohttp.request('GET',
                                          cls.EP_URI,
                                          params={'type': 'mobile-radio',
                                                  'format': 'json',
                                                  'itemId': ep_id})
        data = yield from resp.json()
        import ipdb; ipdb.set_trace()
        pass

    def __init__(self):
        pass


class Programme():
    def __init__(self):
        pass


class RTE():
    SEARCH_URI = 'http://feeds.rasset.ie/rteavgen/search/'

    @staticmethod
    def tag(t):
        return '{http://www.w3.org/2005/Atom}' + t

    def __init__(self):
        pass

    def search(self, query):
        resp = yield from aiohttp.request('GET',
                                          self.SEARCH_URI,
                                          params={'type': 'mobile-radio',
                                                  'query': query})
        data = yield from resp.read()
        dom = fromstring(data)
        for ep_id in dom.iterfind('.//' + self.tag('entry') + '/' + self.tag('id')):
            yield from Episode.from_id(ep_id)


if __name__ == "__main__":
    rte = RTE()
    loop = asyncio.get_event_loop()
    data = loop.run_until_complete(rte.search('taobh'))

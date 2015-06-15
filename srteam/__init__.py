import time
import datetime
import aiohttp
import asyncio
from xml.etree.ElementTree import fromstring
import requests
import m3u8
import os
from typing import List, Optional, TypeVar

URI = str
Tag = str
Path = str
EpisodeID = str
EpisodeInstance = TypeVar('Episode')
Semaphore = Optional[asyncio.Semaphore]


class Stream():
    def __init__(self, uri: URI):
        self._uri = requests.utils.urlparse(uri)
        self.base_uri = '{}/{}'.format(self._uri.hostname,
                                       os.path.dirname(self._uri.path))
        self.base_name = os.path.basename(self._uri.path).replace('.m3u8', '')
        self.uri = self._uri.geturl()
        try:
            resp = requests.get(self.uri)
        except Exception:
            raise Exception("Bad URI")
        try:
            self._stream = m3u8.M3U8(resp.text, base_uri=self.base_uri)
        except Exception:
            raise Exception("Bad stream")
        else:
            self._segments = self._stream.segments
            if not self._segments:
                raise Exception("Bad stream - no segments")

    def _fetch_segment(self,
                       segment: m3u8.Segment,
                       semaphore: asyncio.Semaphore) -> bytes:
        data = None
        for retry in range(10):
            with (yield from semaphore):
                try:
                    uri = segment.absolute_uri
                    if not uri.startswith('http://'):
                        uri = 'http://' + uri
                    print('FETCH', segment.uri)
                    response = yield from aiohttp.request('GET',
                                                          uri)
                except Exception:
                    pass
                else:
                    data = yield from response.read()
                    response.close()
                    break
        return data

    def _fetch(self) -> List[bytes]:
        semaphore = asyncio.Semaphore(10)
        tasks = []
        for segment in self._segments:
            task = asyncio.Task(self._fetch_segment(segment,
                                                    semaphore))
            tasks.append(task)
        return (yield from asyncio.gather(*tasks))

    def save(self, path: Optional[Path]=None) -> Path:
        if path is None:
            path = os.path.join(os.getcwd(), self.base_name)
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(self._fetch())
        with open(path, 'wb') as f:
            for d in data:
                f.write(d)
        return path


class Episode():
    EP_URI = 'http://feeds.rasset.ie/rteavgen/playlist/'
    TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

    @classmethod
    def from_id(cls: EpisodeInstance,
                ep_id: EpisodeID,
                semaphore: Semaphore=None)-> List[EpisodeInstance]:
        if semaphore is None:
            semaphore = asyncio.Semaphore()
        with (yield from semaphore):
            resp = yield from aiohttp.request('GET',
                                              cls.EP_URI,
                                              params={'type': 'mobile-radio',
                                                      'format': 'json',
                                                      'itemId': ep_id})
            data = yield from resp.json()
            episodes = []
            for show in data['shows']:
                server = show['media:group'][0]['rte:server']
                path = show['media:group'][0]['url']
                meta_uri = server + path
                meta_resp = yield from aiohttp.request('GET',
                                                       meta_uri)
                redirect = yield from meta_resp.text()
                uri = redirect.splitlines()[-1]

                ms = int(show['media:group'][0]['duration'])
                duration = datetime.timedelta(seconds=ms / 1000)
                ts = time.mktime(time.strptime(show['valid_start'],
                                               cls.TIME_FORMAT))
                when = datetime.date.fromtimestamp(ts)
                episode = cls(title=show.get('title', ''),
                              desc=show.get('description', ''),
                              channel=show.get('channel', ''),
                              when=when,
                              duration=duration,
                              uri=uri,
                              ep_id=ep_id)
                episodes.append(episode)
            return episodes

    def __init__(self,
                 title: str,
                 desc: str,
                 channel: str,
                 when: datetime.date,
                 duration: datetime.timedelta,
                 uri: URI,
                 ep_id: EpisodeID):
        self.title = title
        self.desc = desc
        self.channel = channel
        self.when = when
        self.duration = duration
        self.uri = uri
        self.ep_id = ep_id

    def __str__(self) -> str:
        return '"{}" {} [{}]'.format(self.title, self.when, self.ep_id)

    def __repr__(self) -> str:
        return '<Episode {}>'.format(self)

    def download(self) -> Path:
        stream = Stream(self.uri)
        return stream.save()


class Srteam():
    SEARCH_URI = 'http://feeds.rasset.ie/rteavgen/search/'

    @staticmethod
    def tag(t: Tag) -> Tag:
        return '{http://www.w3.org/2005/Atom}' + t

    @asyncio.coroutine
    def _do_search(self, query: str, limit: int):
        semaphore = asyncio.Semaphore(10)
        tasks = []
        resp = yield from aiohttp.request('GET',
                                          self.SEARCH_URI,
                                          params={'type': 'mobile-radio',
                                                  'query': query})
        data = yield from resp.read()
        dom = fromstring(data)
        count = 0
        xpath = './/' + self.tag('entry') + '/' + self.tag('id')
        for ep_id in dom.iterfind(xpath):
            count += 1
            tasks.append(asyncio.Task(Episode.from_id(ep_id.text, semaphore)))
            if count >= limit:
                break
        return (yield from asyncio.gather(*tasks))

    def search(self, query: str, limit: Optional[int]=None):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._do_search(query, limit))

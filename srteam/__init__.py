import requests
import asyncio
import aiohttp
import m3u8
import os


class Playlist():
    def __init__(self, uri):
        self._uri = requests.utils.urlparse(playlist_uri)
        self.base_uri = '{}/{}'.format(self._uri.hostname,
                                       os.path.dirname(self._uri.path))
        self.base_name = os.path.basename(self._uri.path).replace('.m3u8', '')
        self.uri = self._uri.geturl()
        try:
            resp = requests.get(self.uri)
        except Exception:
            raise Exception("Bad URI")
        try:
            self._playlist = m3u8.M3U8(resp.text, base_uri=self.base_uri)
            self._segments = self._playlist.segments
        except Exception:
            raise Exception("Bad playlist")

    def _fetch_segment(self, segment, semaphore, connector):
        data = None
        for retry in range(10):
            with (yield from semaphore):
                try:
                    uri = 'http://' + segment.absolute_uri
                    print('FETCH', segment.uri)
                    response = yield from aiohttp.request('GET',
                                                          uri,
                                                          connector=connector)
                except Exception:
                    pass
                else:
                    data = yield from response.read()
                    response.close()
                    break
        return data

    def _fetch(self, connector):
        semaphore = asyncio.Semaphore(10)
        tasks = []
        for segment in self._segments:
            task = asyncio.Task(self._fetch_segment(segment,
                                                    semaphore,
                                                    connector))
            tasks.append(task)
        return (yield from asyncio.gather(*tasks))

    def save(self, path=None):
        if path is None:
            path = os.path.join(os.getcwd(), self.base_name)
        loop = asyncio.get_event_loop()
        connector = aiohttp.TCPConnector(share_cookies=True, loop=loop)
        data = loop.run_until_complete(self._fetch(connector))
        with open(path, 'wb') as f:
            for d in data:
                f.write(d)


if __name__ == "__main__":
    playlist_uri = "http://vodhls.rasset.ie/hls-vod/audio/2015/0614/20150614_rtelyricfm-nova_cl10429017_10431522_261_/20150614_rtelyricfm-nova_cl10429017_10431522_261_.mp4.m3u8"
    p = Playlist(playlist_uri)
    p.save()
    pass

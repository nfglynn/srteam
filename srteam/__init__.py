import requests
import m3u8
import os


class Playlist():
    def __init__(self, playlist_uri):
        self._playlist_uri = requests.utils.urlparse(playlist_uri)
        self.base_uri = '{}/{}'.format(self._playlist_uri.hostname,
                                       os.path.dirname(self._playlist_uri.path))
        self.base_name = os.path.basename(self._playlist_uri.path)
        self.uri = self._playlist_uri.geturl()
        try:
            resp = requests.get(self.uri)
        except Exception:
            raise Exception("Bad URI")
        try:
            self.playlist = m3u8.M3U8(resp.text, base_uri=self.base_uri)
        except Exception:
            raise Exception("Bad playlist")

    def save(self, path=None):
        if path is None:
            path = os.path.join(os.getcwd(), self.base_name.replace('.m3u8', ''))
        with open(path, 'wb') as f:
            for segment in self.playlist.segments:
                print('.', end='')
                resp = requests.get('http://' + segment.absolute_uri)
                f.write(resp.content)


if __name__ == "__main__":
    playlist_uri = "http://vodhls.rasset.ie/hls-vod/audio/2015/0614/20150614_rtelyricfm-nova_cl10429017_10431522_261_/20150614_rtelyricfm-nova_cl10429017_10431522_261_.mp4.m3u8"
    p = Playlist(playlist_uri)
    p.save()
    pass

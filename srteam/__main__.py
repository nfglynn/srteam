import sys

from .__init__ import Srteam

if __name__ == "__main__":
    streamer = Srteam()
    eps = streamer.search(sys.argv[1], limit=5)
    for ep in eps:
        ep[0].download()

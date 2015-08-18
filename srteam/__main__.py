import sys

from .__init__ import Srteam

if __name__ == "__main__":
    streamer = Srteam()
    if len(sys.argv) == 3:
        limit = int(sys.argv[2])
    else:
        limit = 5
    eps = streamer.search(sys.argv[1], limit=limit)
    for ep in eps:
        ep[0].download()

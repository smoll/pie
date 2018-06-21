from logzero import logger, loglevel
from providers import doordash, postmates, seamless, ubereats

loglevel(20)

coords = dict(lat=40.68828329999999, lng=-73.98899849999998)

def searchall(coords):
    """Search all sequentially."""
    doordash.search(**coords)
    postmates.search(**coords)
    seamless.search(**coords)
    ubereats.search(**coords)

# import pdb; pdb.set_trace()
searchall(coords)

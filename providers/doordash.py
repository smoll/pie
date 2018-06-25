from database import dbopen
from logzero import logger
import re
import requests


START_URL = 'https://www.doordash.com/' # GET
ENDPOINT = 'https://api.doordash.com/v2/store_search/' # GET
DEFAULT_PARAMS = {
  'offset': 0,
  'limit': 100,
  'suggest_mode': True,
  'search_items': True,
  'extra': 'stores.address',
}

def reset_tokens():
    logger.info('getting a brand new set of tokens!')
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    }
    response = requests.get(START_URL, headers=headers)
    logger.info('init response=%s' % response)
    logger.debug('init response.headers=%s' % (response.headers,))
    response.raise_for_status()
    cookie_str = response.headers['Set-Cookie']
    matches = re.findall(r'([^,;\s]*csrf[^=]*)=([^,;\s]+)', cookie_str)
    key, val = matches[0]
    keyval = '%s=%s' % (key, val)

    with dbopen() as cur:
        query = """
        UPDATE tokens
        SET token1 = ?, token2 = ?
        WHERE provider = 'doordash';
        """
        cur.execute(query, [keyval, val])

    return get_tokens()

def get_tokens():
    """Init csrf token."""
    with dbopen() as cur:
        cur.execute("SELECT token1, token2 FROM tokens WHERE provider = 'doordash';")
        token1, token2 = cur.fetchone()

        if not token1 or not token2:
            return reset_tokens()

        return (token1, token2)


def search(lat, lng, page_info=None):
    logger.info('searching with kwargs: %s' % (dict(lat=lat, lng=lng, page_info=type(page_info),),))

    params = {'lat': lat, 'lng': lng}
    if isinstance(page_info, dict):
        offset = page_info['next_offset']
        if not offset:
            return # stop condition
        params['offset'] = offset

    token1, token2 = get_tokens()

    headers = {
        'Cookie': token1,
        'X-CSRFToken': token2,
        'Pragma': 'no-cache',
        'Origin': 'https://www.doordash.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Client-Version': 'web version 2.0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
        'Accept': 'application/json',
        'Cache-Control': 'no-cache',
        'Referer': 'https://www.doordash.com/',
        'Connection': 'keep-alive',
    }
    response = requests.get(ENDPOINT, headers=headers, params={**DEFAULT_PARAMS, **params})
    logger.info('fin response=%s' % response)
    logger.debug('fin response.json=%s' % (response.json(),))

    if not response.ok:
        token1, token2 = reset_tokens()
        headers['Cookie'] = token1
        headers['X-CSRFToken'] = token2
        response = requests.get(ENDPOINT, headers=headers, params={**DEFAULT_PARAMS, **params})
        logger.info('fin response=%s' % response)
        logger.debug('fin response.json=%s' % (response.json(),))
        response.raise_for_status()

    return response

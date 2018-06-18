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

# TODO: parameterize
kwargs = {
    "lat": 40.68828329999999,
    "lng": -73.98899849999998,
}


## init csrf token

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
logger.info('init response.headers=%s' % (response.headers,))

cookie_str = response.headers['Set-Cookie']
matches = re.findall(r'([^,;\s]*csrf[^=]*)=([^,;\s]+)', cookie_str)
key, val = matches[0]
keyval = '%s=%s' % (key, val)


## actual data

headers = {
    'Cookie': keyval,
    'X-CSRFToken': val,
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

params = {**DEFAULT_PARAMS, **kwargs}
response = requests.get(ENDPOINT, headers=headers, params=params)
logger.info('fin response=%s' % response)
logger.info('fin response.headers=%s' % (response.json(),))

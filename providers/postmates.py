from logzero import logger
import json
import re
import requests


START_URL = 'https://postmates.com/_/defaults/location'
ENDPOINT = 'https://postmates.com/feed'
COMMON_PARAMS = {
  'client': 'customer.web',
  'version': '3.0.0',
}

# TODO: parameterize
kwargs = {
    "lat": 40.68828329999999,
    "lng": -73.98899849999998,
}

data = json.dumps(kwargs)

logger.info('data=%s' % (data,))

## init location

headers = {
    'origin': 'https://postmates.com',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'x-requested-with': 'XMLHttpRequest',
    'pragma': 'no-cache',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    'content-type': 'application/json',
    'accept': 'application/json, text/plain, */*',
    'cache-control': 'no-cache',
    'authority': 'postmates.com',
    'referer': 'https://postmates.com/',
}

response = requests.post(START_URL, headers=headers, params=COMMON_PARAMS, data=data)

logger.info('init response=%s' % response)
logger.info('init response.headers=%s' % (response.headers,))

cookie_str = response.headers['Set-Cookie']
matches = re.findall(r'([^,;\s]*sesh[^=]*)=([^,;\s]+)', cookie_str)
key, val = matches[0]
keyval = '%s=%s' % (key, val)

# logger.info('keyval: %s' % (keyval,))

## actual data

headers = {
    'origin': 'https://postmates.com',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'x-requested-with': 'XMLHttpRequest',
    'cookie': keyval,
    'content-length': '0',
    'pragma': 'no-cache',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded',
    'accept': 'application/json', # WARNING: must be JSON only!
    'cache-control': 'no-cache',
    'authority': 'postmates.com',
    'referer': 'https://postmates.com/food', # WARNING: prod uses /feed instead of /food... is this being deprecated?
}

response = requests.post(ENDPOINT, headers=headers, params=COMMON_PARAMS)
logger.info('fin response=%s' % response)
logger.info('fin response.headers=%s' % (response.json(),))

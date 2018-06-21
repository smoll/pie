from logzero import logger
import json
import re
import requests


START_URL = 'https://postmates.com/_/defaults/location' # POST
ENDPOINT = 'https://postmates.com/feed' # POST
COMMON_PARAMS = {
  'client': 'customer.web',
  'version': '3.0.0',
}

def search(lat, lng):
    ## init location
    data = json.dumps({'lat': lat, 'lng': lng})
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
    logger.debug('init response.headers=%s' % (response.headers,))
    cookie_str = response.headers['Set-Cookie']
    matches = re.findall(r'([^,;\s]*sesh[^=]*)=([^,;\s]+)', cookie_str)
    key, val = matches[0]
    keyval = '%s=%s' % (key, val)
    logger.debug('keyval: %s' % (keyval,))

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
    logger.debug('fin response.json=%s' % (response.json(),))
    return response

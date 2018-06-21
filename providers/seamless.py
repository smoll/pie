from logzero import logger
from random import randint
import json
import requests


START_URL = 'https://api-gtm.grubhub.com/auth' # POST
ENDPOINT = 'https://api-gtm.grubhub.com/restaurants/search' # GET
DEFAULT_HEADERS = {
  'Pragma': 'no-cache',
  'Origin': 'https://www.seamless.com',
  'Accept-Encoding': 'gzip, deflate, br',
  'Accept-Language': 'en-US,en;q=0.9',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
  'Content-Type': 'application/json',
  'Accept': 'application/json, text/plain, */*',
  'Cache-Control': 'no-cache',
  'Referer': 'https://www.seamless.com',
  'Connection': 'keep-alive',
}
LIMIT = 100

def _digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def search(lat, lng):
    ## init access token
    payload = {
        "brand": "SEAMLESS",
        "client_id": "beta_seamless_ayNyuFxxVQYefSAhFYCryvXBPQc",
        "device_id": _digits(10),
        "scope": "anonymous"
    }
    data = json.dumps(payload)
    response = requests.post(START_URL, headers=DEFAULT_HEADERS, data=data)
    logger.info('init response=%s' % response)
    logger.debug('init response.headers=%s' % (response.headers,))
    # import pdb; pdb.set_trace()
    token = response.json()['session_handle']['access_token']

    ## actual data
    point = 'POINT(%s %s)' % (lng, lat)
    payload = {
        'orderMethod': 'delivery',
        'locationMode': 'DELIVERY',
        'facetSet': 'umamiV2',
        'pageSize': LIMIT,
        'hideHateos': 'true',
        'searchMetrics': 'true',
        # 'queryText': 'pizza', # search by cuisine
        'location': point,
        'facet': 'open_now:true',
        'variationId': 'imUseDefaultForPickup',
        # 'fieldSet': 'cuisine', # search by cuisine
        'sortSetId': 'umamiV2', # previously: umamiV2_imGhostChili
        'sponsoredSize': '2',
        'countOmittingTimes': 'true',
    }
    headers = {
        **DEFAULT_HEADERS,
        'Authorization': 'Bearer %s' % token,
        'If-Modified-Since': '0',
    }
    response = requests.get(ENDPOINT, headers=headers, params=payload)
    logger.info('fin response=%s' % response)
    logger.debug('fin response.json=%s' % (response.json(),))
    return response

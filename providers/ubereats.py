from logzero import logger
import json
import re
import requests


START_URL = 'https://www.ubereats.com/' # GET
ENDPOINT = 'https://www.ubereats.com/rtapi/eats/v1/allstores' # POST
LIMIT = 100


# TODO: parameterize
kwargs = {
    "lat": 40.68828329999999,
    "lng": -73.98899849999998,
}


## init session cookie + csrf token

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
# logger.info('init response.headers=%s' % (response.headers,))

cookie_str = response.headers['Set-Cookie']
matches = re.findall(r'([^,;\s]*sess[^=]*)=([^,;\s]+)', cookie_str)
key, val = matches[0]
keyval = '%s=%s' % (key, val)
logger.info('keyval: %s' % keyval)


## actual data

cookies = {key: val}
headers = {
    'Origin': 'https://www.ubereats.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-csrf-token': response.headers['x-csrf-token'],
    'accept-language': 'en-US',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
    'content-type': 'application/json',
    'Accept': '*/*',
    'Referer': 'https://www.ubereats.com/stores/',
    'Connection': 'keep-alive',
}
params = (
    ('plugin', 'StorefrontFeedPlugin'),
)
data = {
    "targetLocation":{
      "latitude": kwargs['lat'],
      "longitude": kwargs['lng'],
      # "reference":"ChIJVXiogbRdwokR9Z7FmoJGVtI",
      # "type":"google_places",
      # "address":{"title":"2928 Atlantic Ave","address1":"2928 Atlantic Ave, Brooklyn"}
    },
    "feed":"combo",
    "feedTypes":["STORE","SEE_ALL_STORES"],
    "feedVersion":2,
    "pageInfo":{
        "offset":0,
        "pageSize":LIMIT,
    },
}
response = requests.post('https://www.ubereats.com/rtapi/eats/v1/allstores', headers=headers, params=params, cookies=cookies, data=json.dumps(data))

logger.info('fin response=%s' % response)
logger.info('fin response.headers=%s' % (response.json(),))

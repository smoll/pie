from database import dbopen
from loader import Loader
from logzero import logger
from pandas.io.json import json_normalize
import json
import re
import requests


class UberEats:
    SHORTNAME = 'uber_eats'
    START_URL = 'https://www.ubereats.com/' # GET
    ENDPOINT = 'https://www.ubereats.com/rtapi/eats/v1/allstores' # POST
    LIMIT = 100

    def __init__(self):
        self.response = None
        self.data = None
        self.more = None
        self.loader = Loader(self.SHORTNAME, 'uuid')

    def _reset_tokens(self):
        logger.info('getting a brand new set of tokens!')
        ## init session cookie + csrf token
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
        }
        response = requests.get(self.START_URL, headers=headers)

        logger.info('init response=%s' % response)
        logger.debug('init response.headers=%s' % (response.headers,))
        cookie_str = response.headers['Set-Cookie']
        matches = re.findall(r'([^,;\s]*sess[^=]*)=([^,;\s]+)', cookie_str)
        key, val = matches[0]
        cookie = '%s=%s' % (key, val)
        logger.debug('cookie: %s' % cookie)
        csrf_token = response.headers['x-csrf-token']

        with dbopen() as cur:
            query = f"""
            UPDATE tokens
            SET token1 = ?, token2 = ?
            WHERE provider = '{self.SHORTNAME}';
            """
            cur.execute(query, [cookie, csrf_token])

        return (cookie, csrf_token)


    def _get_tokens(self):
        """Get stored tokens."""
        with dbopen() as cur:
            cur.execute("SELECT token1, token2 FROM tokens WHERE provider = '%s';" % self.SHORTNAME)
            cookie, csrf_token = cur.fetchone()

            if not cookie or not csrf_token:
                return self._reset_tokens()

            return (cookie, csrf_token)


    def search(self, lat, lng, more={}):
        logger.info('searching with kwargs: %s' % (dict(lat=lat, lng=lng, more=type(more),),))

        if more is None:
            self.response = None
            self.data = None
            self.more = None
            logger.warn('nothing left to do!')
            return

        offset = int(more.get('offset', 0))
        data = {
            "targetLocation":{
              "latitude": lat,
              "longitude": lng,
              # "reference":"ChIJVXiogbRdwokR9Z7FmoJGVtI",
              # "type":"google_places",
              # "address":{"title":"2928 Atlantic Ave","address1":"2928 Atlantic Ave, Brooklyn"}
            },
            "feed": "combo",
            "feedTypes": ["STORE","SEE_ALL_STORES"],
            "feedVersion": 2,
            "pageInfo": {
                "offset": offset,
                "pageSize": self.LIMIT,
            },
        }

        cookie, csrf_token = self._get_tokens()

        ## actual data
        cookies = dict([cookie.split('=')])
        headers = {
            'Origin': 'https://www.ubereats.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'x-csrf-token': csrf_token,
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
        response = requests.post(self.ENDPOINT, headers=headers, params=params, cookies=cookies, data=json.dumps(data))
        logger.info('fin response=%s' % response)

        if not response.ok:
            cookie, csrf_token = self._reset_tokens()
            cookies = dict([cookie.split('=')])
            headers['x-csrf-token'] = csrf_token
            response = requests.post(self.ENDPOINT, headers=headers, params=params, cookies=cookies, data=json.dumps(data))
            logger.info('retried fin response=%s' % response)
            response.raise_for_status()

        logger.debug('fin response.json=%s' % (response.json(),))

        self.response = response
        self.data = response.json()
        items = len(self.data['feed']['feedItems']) if 'feedItems' in self.data['feed'] else 0
        self.more = {'offset': offset + items} if items else None

        return response


    def save_data(self):
        if self.data is None:
            return
        elif 'feedItems' not in self.data['feed']:
            logger.warn('zero results from uber_eats query.')
            return
        stores = self.data['feed']['feedItems']
        columns_to_drop = [
            'payload_storePayload_stateMapDisplayInfo_available_heroImage_items',
        ]
        df = json_normalize(stores)
        df.rename(columns=lambda x: x.replace('.', '_'), inplace=True)
        df.drop(columns=[c for c in columns_to_drop if c in df.columns], inplace=True)
        logger.debug('columns: %s' % (df.columns,))
        self.loader.load_data(df)

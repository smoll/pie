from database import dbopen
from loader import Loader
from logzero import logger
from pandas.io.json import json_normalize
import re
import requests


class DoorDash:
    SHORTNAME = 'door_dash'
    START_URL = 'https://www.doordash.com/' # GET
    ENDPOINT = 'https://api.doordash.com/v2/store_search/' # GET
    DEFAULT_PARAMS = {
      'offset': 0,
      'limit': 100,
      'suggest_mode': True,
      'search_items': True,
      'extra': 'stores.address',
    }


    def __init__(self):
        self.response = None
        self.data = None
        self.loader = Loader(table=self.SHORTNAME)


    def search(self, lat, lng, page_info=None):
        logger.info('searching with kwargs: %s' % (dict(lat=lat, lng=lng, page_info=type(page_info),),))

        params = {'lat': lat, 'lng': lng}
        if isinstance(page_info, dict):
            offset = page_info['next_offset']
            if not offset:
                # stop condition
                self.response = None
                self.data = None
                return
            params['offset'] = offset

        token1, token2 = self._get_tokens()

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
        response = requests.get(self.ENDPOINT, headers=headers, params={**self.DEFAULT_PARAMS, **params})
        logger.info('fin response=%s' % response)
        logger.debug('fin response.json=%s' % (response.json(),))

        if not response.ok:
            token1, token2 = self._reset_tokens()
            headers['Cookie'] = token1
            headers['X-CSRFToken'] = token2
            response = requests.get(self.ENDPOINT, headers=headers, params={**self.DEFAULT_PARAMS, **params})
            logger.info('retried fin response=%s' % response)
            logger.debug('retried fin response.json=%s' % (response.json(),))
            response.raise_for_status()

        self.response = response
        self.data = response.json()
        return response


    def save_data(self):
        if self.data is None:
            return
        stores = self.data['stores']
        columns_to_drop = [
            'menus',
            'merchant_promotions',
            'status_asap_minutes_range',
        ]
        df = json_normalize(stores)
        df.rename(columns=lambda x: x.replace('.', '_'), inplace=True)
        df.drop(columns=columns_to_drop, inplace=True)
        logger.debug('columns: %s' % (df.columns,))
        self.loader.load_data(df)


    def _reset_tokens(self):
        logger.info('getting a brand new set of tokens!')
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
        response.raise_for_status()
        cookie_str = response.headers['Set-Cookie']
        matches = re.findall(r'([^,;\s]*csrf[^=]*)=([^,;\s]+)', cookie_str)
        key, val = matches[0]
        keyval = '%s=%s' % (key, val)

        with dbopen() as cur:
            query = """
            UPDATE tokens
            SET token1 = ?, token2 = ?
            WHERE provider = '%s';
            """ % self.SHORTNAME
            cur.execute(query, [keyval, val])

        return (keyval, val)


    def _get_tokens(self):
        """Init csrf token."""
        with dbopen() as cur:
            cur.execute("SELECT token1, token2 FROM tokens WHERE provider = '%s';" % self.SHORTNAME)
            token1, token2 = cur.fetchone()

            if not token1 or not token2:
                return self._reset_tokens()

            return (token1, token2)

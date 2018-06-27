from database import dbopen
from loader import Loader
from logzero import logger
from pandas.io.json import json_normalize
from random import randint
import json
import requests

def _digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

class Seamless:
    SHORTNAME = 'seamless'
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


    def __init__(self):
        self.response = None
        self.data = None
        self.more = None
        self.loader = Loader(self.SHORTNAME, 'uid')


    def _reset_token(self):
        logger.info('getting a brand new set of tokens!')
        ## init access token
        payload = {
            "brand": "SEAMLESS",
            "client_id": "beta_seamless_ayNyuFxxVQYefSAhFYCryvXBPQc",
            "device_id": _digits(10),
            "scope": "anonymous"
        }
        data = json.dumps(payload)
        response = requests.post(self.START_URL, headers=self.DEFAULT_HEADERS, data=data)
        logger.info('init response=%s' % response)
        logger.debug('init response.headers=%s' % (response.headers,))
        token = response.json()['session_handle']['access_token']

        with dbopen() as cur:
            query = f"""
            UPDATE tokens
            SET token1 = ?
            WHERE provider = '{self.SHORTNAME}';
            """
            cur.execute(query, [token])

        return token


    def _get_token(self):
        """Init csrf token."""
        with dbopen() as cur:
            cur.execute("SELECT token1 FROM tokens WHERE provider = '%s';" % self.SHORTNAME)
            token = cur.fetchone()[0]

            if not token:
                return self._reset_token()

            return token


    def search(self, lat, lng, more={}):
        """
        Search a given (lat, lng).
        If more is None, do nothing.
        """
        logger.info('searching with kwargs: %s' % (dict(lat=lat, lng=lng, more=type(more),),))

        if more is None:
            self.response = None
            self.data = None
            self.more = None
            logger.warn('nothing left to do!')
            return

        token = self._get_token()
        # import pdb; pdb.set_trace()

        ## actual data
        point = 'POINT(%s %s)' % (lng, lat)
        payload = {
            'orderMethod': 'delivery',
            'locationMode': 'DELIVERY',
            'facetSet': 'umamiV2',
            'pageSize': self.LIMIT,
            'pageNum': int(more.get('page', 1)),
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
            **self.DEFAULT_HEADERS,
            'Authorization': 'Bearer %s' % token,
            'If-Modified-Since': '0',
        }
        response = requests.get(self.ENDPOINT, headers=headers, params=payload)
        logger.info('fin response=%s' % response)

        if not response.ok:
            token = self._reset_token()
            headers['Authorization'] = 'Bearer %s' % token
            response = requests.get(self.ENDPOINT, headers=headers, params=payload)
            logger.info('retried fin response=%s' % response)
            response.raise_for_status()

        logger.debug('fin response.json=%s' % (response.json(),))

        self.response = response
        self.data = response.json()
        pager = self.data['search_result']['pager']
        self.more = {'page': pager['current_page'] + 1} if pager['current_page'] < pager['total_pages'] else None

        return response


    def save_data(self):
        if self.data is None:
            return
        stores = self.data['search_result']['results']
        columns_to_drop = [
            'badge_list',
            'faceted_rating_data_faceted_rating_list',
            'highlighting_info',
            'menu_items',
        ]
        df = json_normalize(stores)
        df.rename(columns=lambda x: x.replace('.', '_'), inplace=True)
        df.drop(columns=[c for c in columns_to_drop if c in df.columns], inplace=True)
        df['cuisines'] = df['cuisines'].apply(', '.join) # HACK: convert from list to comma-separated string so we can store it
        logger.debug('columns: %s' % (df.columns,))
        # import pdb; pdb.set_trace()
        self.loader.load_data(df)

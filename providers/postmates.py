from loader import Loader
from logzero import logger
from pandas.io.json import json_normalize
import json
import re
import requests


class Postmates:
    SHORTNAME = 'postmates'
    START_URL = 'https://postmates.com/_/defaults/location' # POST
    ENDPOINT = 'https://postmates.com/_/feed/nearby' # POST
    COMMON_PARAMS = {
      'client': 'customer.web',
      'version': '3.0.0',
    }


    def __init__(self):
        self.response = None
        self.data = None
        self.more = None
        self.loader = Loader(self.SHORTNAME, 'uuid')


    def search(self, lat, lng, more={}):
        """
        Search a given (lat, lng) and set self.data to the decoded response data.
        If more is None, do nothing.
        """
        logger.info('searching with kwargs: %s' % (dict(lat=lat, lng=lng, more=type(more),),))

        if more is None:
            self.response = None
            self.data = None
            self.more = None
            logger.warn('nothing left to do!')
            return

        req_data = {
            'fulfillment_type': 'delivery',
            'page': int(more.get('page', 1)),
        }
        # import pdb; pdb.set_trace()
        logger.info('req_data: %s' % (req_data,))

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
        response = requests.post(self.START_URL, headers=headers, params=self.COMMON_PARAMS, data=data)
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
        response = requests.post(self.ENDPOINT, headers=headers, params=self.COMMON_PARAMS, data=json.dumps(req_data))
        logger.info('fin response=%s' % response)
        logger.debug('fin response.json=%s' % (response.json(),))

        self.response = response
        self.data = response.json()
        self.more = {'page': req_data['page'] + 1} if self.data.get('has_more') else None
        return response


    def save_data(self):
        if self.data is None:
            return
        stores = self.data['items']
        columns_to_drop = [
            'header_img_resolutions',
            'icon_img_resolutions',
            'media_header_img_resolutions',
            'media_icon_img_resolutions',
            'primary_place_category_header_img_resolutions',
            'badges',
            'place_meta_polys',
        ]
        df = json_normalize(stores)
        df.rename(columns=lambda x: x.replace('.', '_'), inplace=True)
        df.drop(columns=[c for c in columns_to_drop if c in df.columns], inplace=True)
        logger.debug('columns: %s' % (df.columns,))
        self.loader.load_data(df)

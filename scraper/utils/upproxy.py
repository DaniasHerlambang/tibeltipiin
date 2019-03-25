# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import json
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROXIES_JSON = os.path.join(BASE_DIR, 'utils/proxies.json')

API_URL = 'http://list.didsoft.com/get?email=fenditricahyono@gmail.com&pass=vyqe9y&pid=http2000'
proxies = requests.get(API_URL).text.split('\n')

if not 'expired' in ''.join(proxies):
    with open(PROXIES_JSON, 'w') as outfile:
        json.dump(proxies, outfile)
else:
    raise Exception(''.join(proxies))

# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import re
import time
import json
import requests

from lxml import html
from random import choice
from .user_agents import userAgents

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROXIES_JSON = os.path.join(BASE_DIR, 'scraper/utils/proxies.json')
MAX_REQUESTS = 3


class ScrapRequest():

    def get_proxy(self):
        start = time.time()
        while (time.time()-start) < 3:
            try:
                with open(PROXIES_JSON) as f:
                    data = json.load(f)
                return data
            except:
                time.sleep(1)
        return self.get_proxies()

    def get(self, URL):
        if not self.url_validator(URL):
            return {"status_code": 406,
                    "message": "Invalid URL"}
        proxies = list(filter(None, self.get_proxy()))
        for i in range(0, MAX_REQUESTS):
            headers = {'User-Agent': choice(userAgents)}
            useproxy = True
            try:
                proxy = {'http': choice(proxies)}
            except:
                useproxy = False

            try:
                if useproxy:
                    req = requests.get(URL, headers=headers, proxies=proxy)
                else:
                    req = requests.get(URL, headers=headers)
                if req.status_code == 200:
                    if 'discuss automated' not in req.text and 'Robot Check' not in req.text:
                        return {"status_code": req.status_code,
                                "content": req}

            except requests.exceptions.ConnectionError:
                return {"status_code": "Connection Refused"}

            i = i + 1

        return {"status_code": 400,
                "message": "Fail"}

    def url_validator(self, URL):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            # domain...
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(regex, URL) is not None

    def get_proxies(self):
        url = 'https://free-proxy-list.net/'
        response = requests.get(url)
        parser = html.fromstring(response.text)
        proxies = []
        for i in parser.xpath('//tbody/tr')[:10]:
            if i.xpath('.//td[7][contains(text(),"yes")]'):
                proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
                proxies.append(proxy)
        return proxies

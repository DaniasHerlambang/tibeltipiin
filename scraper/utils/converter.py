# -*- coding: utf-8 -*-
from __future__ import absolute_import

import time
import requests


def currency(dollar=None, from_money='USD', to_money='IDR'):
    """
    ger currency from currencyconverterapi.com
    """
    params = '?q=%s_%s&compact=ultra&apiKey=043563e3cddd26f84f28' % (from_money, to_money)
    url = 'https://free.currencyconverterapi.com/api/v6/convert{}'.format(params)
    return requests.get(url).json().get('%s_%s' % (from_money, to_money))

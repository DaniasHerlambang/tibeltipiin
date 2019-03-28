# -*- coding: utf-8 -*-

import re
import os
import sys
import json
import js2py
import datetime
import traceback
from lxml import html

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join(BASE_DIR, 'scraper'))

try:
    from base import Scraper
    from utils.lib import ScrapRequest
    from utils.converter import currency
except Exception as error:
    raise error

# NAME ={'xpath': ['//div[@itemprop="name"]//text()']}
NAME = {'xpath': ['//h1[(@class, "heading-5 v-fw-regular")]//text()']}
# CATEGORY = {'xpath': ['//ol[contains(@id="breadcrumb-list")]//a//text()']}
# ORIGINAL_PRICE = {'xpath': ['[contains(@class, "pb-current-price")]//span//text()']}
# DESCRIPTION = {'xpath': ['//div[@id="long-description"]']}

# COUNTRY = {'xpath': ['//span[@itemprop="availableAtOrFrom"]//text()']}
# PRICES = {'xpath': ['//span[@id="prcIsum"]//text()', '//span[@id="mm-saleDscPrc"]']}
# ORIGINAL_PRICE = {'xpath': ['//span[@id="orgPrc"]//text()', '//span[@id="mm-saleOrgPrc"]//text()']}
# AVAILABILITY = {'xpath': ['//span[@id="qtySubTxt"]//text()',  # More than 10 available, Limited quantity available
#                           '//span[@id="qtySubTxt"]/span//text()']}
# IMAGE_URLS = {'xpath': ['//div[@id="vi_main_img_fs"]']}
# IMAGE_URL = {'xpath': ['//img[@id="icImg"]/@src']}


class BestbuyScraper(Scraper):
    print('0')
    def __init__(self, url, raw_response):
        print('a')
        self.url = url
        self.page_text = None
        self.page_content = None
        self.html_content = None

        if raw_response['status_code'] == 200:
            print('b')
            self.page_text = raw_response['content'].text
            self.page_content = raw_response['content'].content
            self.html_content = html.fromstring(self.page_content)

        # initialize from parent to fetch `self.RESPONSE_DATA`
        super().__init__(url)

    def __repr__(self):
        print('c')
        return '%s(url="%s")' % (self.__class__.__name__, self.url)

    def use_x_path(self, path):
        print('d' , path)

        """
        function to enable scrap by using xpath method.

        :param `reg` is regex pattern, like: '//span[@id="vi-lkhdr-itmTitl"]//text()' ...etc
        :return dict of {'value': [<Element div at 0x7f...>], 'method': 'xpath'}
        """
        if self.html_content is not None:
            return {'value': self.html_content.xpath(path), 'method': 'xpath'}
        return {'value': None, 'method': None}

    def use_regex(self, reg):
        """
        function to enable scrap by using regex method.

        :param `reg` is regex pattern, like: [0-9]\w+ ...etc
        :return dict of {'value': ['this is baz'], 'method': 'regex'}
        """
        try:
            print('e')
            out = re.findall(reg, self.page_text)
        except:
            print('f')
            out = None
        print('g')
        return {'value': out, 'method': 'regex'}

    def scrap(self, **kwargs):
        """
        function to scrap by using `xpath` or `regex` mode.

        :param `kwargs` are requires for `field` and `data` parameters.
        :return output result of 'value' or dict of {'value': <FIELD_NAME>, 'method': None}
        """
        field = kwargs['field']
        data = kwargs['data']

        if data:
            if 'xpath' in data:
                if data['xpath']:
                    for xpath in data['xpath']:
                        output = self.use_x_path(xpath)
                        if output['value']:
                            print('h')
                            return output

            if 'regex' in data:
                if data['regex']:
                    for regex in data['regex']:
                        output = self.use_regex(regex)
                        if output['value']:
                            print('i')
                            return output
        print('j')
        return {'value': self.RESPONSE_DATA[field], 'method': None}

    def get_html(self, field_name):
        """
        :param `field_name` is like 'DESCRIPTION'.
        :return string of scrap result for the specific html element.
        """
        field, data = field_name, eval(field_name)
        raw = self.scrap(field=field, data=data)

        try:
            out_html_string = ''
            for element in raw['value']:
                html_tostring = html.tostring(element)
                html_tostring = html_tostring.decode('utf-8')\
                                             .replace('\n', '')\
                                             .replace('\t', '')\
                                             .replace('<script', '<scripta style="display:none"')\
                                             .replace('</script>', '</scripta>')
                out_html_string += html_tostring
            print('k')
            return out_html_string
        except Exception as error:
            return ''

    def get_default(self, field_name):
        """
        :param `field_name` is like 'NAME', 'PRODUCT_ID', etc.
        :return string of scrap result.
        """
        field, data = field_name, eval(field_name)
        raw = self.scrap(field=field, data=data)
        if raw['method'] == None:
            return raw['value']
        return ' '.join(''.join(raw['value']).split()) if raw else None

    def find_price(self, price):
        price = str(price).replace(',', '') if price else ''
        match = re.search(r'[0-9.]+', price)
        if match:
            price = match.group()
        return float(price) if price else None

    # ----------------------------
    # BEGIN OF ABSTRACT FUNCTIONS
    # ----------------------------

    def get_name(self, field_name='NAME'):
        """
        function to get name/title of product
        :return string name of product.
        """
        return self.get_default(field_name)

    def get_product_id(self, field_name='PRODUCT_ID'):
        """
        function to get product id of product
        :return string id of product.
        """
        return self.get_default(field_name)

    def get_product_code(self, field_name='PRODUCT_ID'):
        """
        function to get product code of product
        :return string code of product.
        """
        return self.get_default(field_name)

    def get_country(self, field_name='COUNTRY'):
        """
        function to get product/item location.

        :param `field_name` is field for 'COUNTRY'
        :return string of scrap result for the country.
        """
        pass


    def get_price(self, field_name='PRICES'):
        """
        function to get fixed price of product.
        :return float (eg: 29.83) or None
        """
        price_data = self.get_price_data()
        return price_data.get('price') or self.find_price(self.get_default(field_name))

    def get_prices(self):
        """
        function to get prices of product.
        :return list prices of product.
        """
        price = self.get_price()
        if price:
            return [price]
        return []

    def get_price_dollar(self):
        """
        function to convert the product price into dollar.
        eg: from CNY to USD
        :return float(eg: 29.83) or None
        """
        price = self.get_price()
        currency_code = self.get_currency_code()
        if price and currency_code:
            if currency_code != 'USD':
                return currency(price, from_money=currency_code, to_money='USD')
        return price

    def get_currency_code(self):
        """
        function to get the price code, eg: IDR, USD, GBP, etc.
        :return string of price code or None
        """
        price_data = self.get_price_data()
        return price_data.get('code') or 'USD'

    def get_currency_value(self):
        """
        function to get converted money from eg: 1 USD to IDR
        :return float of currency value or None
        """
        currency_code = self.get_currency_code()
        return currency(1, from_money=currency_code, to_money='IDR')

    def get_category(self, field_name='CATEGORY'):
        """
        function to get category of product.
        :param `field_name` is field for 'CATEGORY'
        :return string of categoryhttps://www.bestbuy.com/site/cricket-wireless-samsung-galaxy-sol-3-with-16gb-memory-prepaid-cell-phone-silver/6215340.p?skuId=6215340
        """
        field, data = field_name, eval(field_name)
        raw = self.scrap(field=field, data=data)
        if raw['method'] == None:
            return raw['value']
        return ', '.join(raw['value']) if raw else None

    def get_availability(self, field_name='AVAILABILITY'):
        """
        function to get product availability
        :return string/text of product availability.
        """
        return self.get_default(field_name)

    def get_image_url(self):
        """
        function to get fist thumbnail image of product.
        :return string url of image
        """
        return self.get_extract_image_urls(is_first=True)

    def get_image_urls(self):
        """
        function to get all thumbnail image urls of product.
        :return list urls of images.
        """
        return self.get_extract_image_urls(is_first=False)

    def get_description(self, field_name='DESCRIPTION'):
        """
        function to get description html of product.
        :param `field_name` is field name for 'DESCRIPTION'
        :return html string of product description.
        """
        return self.get_html(field_name)

    def get_max_quantity(self):
        """
        function to get maximum quantity of product.
        :return integer or None
        """
        try:
            additional_json = self.get_additional_json()
            return additional_json['ActionPanel']['isModel']['remainQty']
        except Exception as error:
            return None

    def get_weight(self):
        """
        function to get weight of product
        :return integer or float
        """
        # FIXME: BELUM ADA KEPUTUSAN
        return 0

    def get_weight_unit(self):
        """https://www.bestbuy.com/site/cricket-wireless-samsung-galaxy-sol-3-with-16gb-memory-prepaid-cell-phone-silver/6215340.p?skuId=6215340
        function to get weight unit, eg: 'gram', 'kg', 'pounds'
        :return string of weight unit, default 'gram'
        """
        return 'gram'  # default

    def get_shipping_weight(self):
        """
        function to get shipping weight if it exist.
        :return integer, float or None
        """
        pass


    def get_dimension_height(self):
        """
        function to get dimension height if it exist.
        :return integer, float or None
        """
        pass

    def get_dimension_width(self):
        """
        function to get dimension width if it exist.
        :return integer, float or None
        """
        pass

    def get_dimension_length(self):
        """
        function to get dimension length if it exist.
        :return integer, float or None
        """
        pass


    def get_dimension_unit(self):
        """
        function to get dimension unit of product, eg: 'cm', 'm'
        :return string of dimension unit, default 'cm'
        """
        return 'cm'  # default

    def get_marketplace(self):
        """
        function to get the name of marketplace, eg: 'amazon.com', 'ebay.com'
        :return string name of marketplace
        """
        return 'bestbuy.com'  # default for this class.BestbuyScraper

    def get_variations(self):
        """
        function to get product variations, eg: price, color, etc.
        :return list of product variations.

        result of this variations is look like this:
        [
          {
            "Leg Length": "L32",
            "Waist Size": "W32",
            "colour": "Light Broken-In",
            "waist_size": "W32",
            "price": 49.9,
            "leg_length": "L32",
            "Colour": "Light Broken-In",
            "ASIN": "610372969221"
          },
          ....
        ]
        """
        return []

    def get_options(self):
        """
        function to get options menu (product selection)
        :return list of selection type

        result of this options is look like this:
        [
          {
            "specification_key": "colour_men",
            "specification": "Colour Men",
            "choices": [
                "Black",
                "Light Broken-In",
                "One Wash",
                "Stonewash"
            ]
          },
          ....
        ]
        """
        additional_data = self.get_additional_data()
        options_out = []
        for key, value in additional_data['DIMENSION_VALUES'].items():
            key_label = ' '.join(key.split('_')).strip().title()
            data = {'specification': key_label, 'specification_key': key, 'choices': value}
            options_out.append(data)
        return options_out

    def get_page_mode(self):
        """
        function to differentiate the page mode,
        for example:
            - amazon scraper using 'reload'
            - ebay scraper using 'combination'

        :return string of 'combination', 'reload' or etc.
        """
        return 'combination'


if __name__ == '__main__':
    try:
        url = 'https://www.bestbuy.com/site/cricket-wireless-samsung-galaxy-sol-3-with-16gb-memory-prepaid-cell-phone-silver/6215340.p?skuId=6215340'
        if len(sys.argv) > 1:
            print('1')
            url = sys.argv[-1]
        raw_response = ScrapRequest().get(url)
        print('2')
        scraper = BestbuyScraper(url, raw_response)
        response = scraper.get_result()
    except Exception as error:
        response = {'action': False, 'error_message': str(error)}

    print(response)

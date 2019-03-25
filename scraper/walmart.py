# -*- coding: utf-8 -*-

import re
import os
import sys
import json
import js2py
import datetime
import traceback
from lxml import html
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join(BASE_DIR, 'scraper'))

try:
    from base import Scraper
    from utils.lib import ScrapRequest
    from utils.converter import currency
except Exception as error:
    raise error


NAME = {'xpath': ['//h1[contains(@class, "prod-ProductTitle")]//text()']}
PRICE = {'xpath': ['//div[contains(@class, "product-offer-price")]//*'
                   '//span[contains(@class, "price-characteristic")]/@content']}
CURRENCY_CODE = {'xpath': ['(//span[contains(@class, "price-currency")]/@content)[1]']}
CATEGORY = {'xpath': ['//ol[contains(@class, "breadcrumb-list")]//a//text()']}


class WalmartScraper(Scraper):

    def __init__(self, url, raw_response):
        self.url = url
        self.page_text = None
        self.page_content = None
        self.html_content = None
        self.additional_json = {}

        if raw_response['status_code'] == 200:
            self.page_text = raw_response['content'].text
            self.page_content = raw_response['content'].content
            self.html_content = html.fromstring(self.page_content)

        # initialize from parent to fetch `self.RESPONSE_DATA`
        super().__init__(url)

    def __repr__(self):
        return '%s(url="%s")' % (self.__class__.__name__, self.url)

    def use_x_path(self, path):
        """
        function to enable scrap by using xpath method.

        :param `reg` is regex pattern, like: '//span[@id="vi-lkhdr-itmTitl"]//text()' ...etc
        :return dict of {'value': [<Element div at 0x7f...>], 'method': 'xpath'}
        """
        return {'value': self.html_content.xpath(path), 'method': 'xpath'}

    def use_regex(self, reg):
        """
        function to enable scrap by using regex method.

        :param `reg` is regex pattern, like: [0-9]\w+ ...etc
        :return dict of {'value': ['this is baz'], 'method': 'regex'}
        """
        try:
            out = re.findall(reg, self.page_text)
        except:
            out = None
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
                            return output

            if 'regex' in data:
                if data['regex']:
                    for regex in data['regex']:
                        output = self.use_regex(regex)
                        if output['value']:
                            return output

        return {'value': self.RESPONSE_DATA[field], 'method': None}

    def get_html(self, field_name):
        """
        :param `field_name` is like 'DESCRIPTION', 'INFORMATION', etc.
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

    def get_additional_json(self):
        """
        major data for walmart
        """
        # using this `xpath` we got an error when the text having
        # double quote inside double quotes, eg: "Lorem Ipsum dolor" ismet"
        # xpath_query = '//script[@id="tb-djs-wml-redux-state"]//text()'
        # scripts = self.html_content.xpath(xpath_query)

        soup = BeautifulSoup(self.page_text, 'html.parser')
        script = soup.find('script', {'id': 'tb-djs-wml-redux-state'})

        try:
            additional_json = json.loads(script.text)
        except Exception:
            additional_json = {}

        # assign into self variable `self.additional_json`
        # so, this `self.get_additional_json()` fucntion not to be called many times
        # we call this function only once first call in `self.product_info()`
        self.additional_json = additional_json

        return additional_json

    def get_product_info(self):
        """
        "productBasicInfo": {
            "selectedProductId": "5WHBQ9KMJ96U",
            "5WHBQ9KMJ96U": {
              "title": "Roadmaster 24\" Granite Peak Boy's Mountain Bike, Silver",
              "brand": "ROADMASTER",
              "type": "VARIANT",
              "rhPath": "30000:34000:34001:34101:34215",
              "catPath": "Home Page/Sports & Outdoors/Bikes/Adult Bikes/Mountain Bikes/All Mountain Bikes",
              "imageUrl": "https://i5.walmartimages.com/asr/9e225f78-8d31-44f3-b60e-07a98dcb0bc3_1.3787fb7513b1f8d913d1535e0565c9ab.jpeg?odnHeight=100&odnWidth=100&odnBg=FFFFFF",
              "usItemId": "715396317",
              "productId": "5WHBQ9KMJ96U",
              "upc": "038675137776",
              "wupc": "0003867513777",
              "manufacturer": "Pacific Cycle",
              "selectedVariant": [
                {
                  "name": "24\" Boy's",
                  "isImageSwatch": false,
                  "swatchImageUrl": ""
                }
              ]
            },
            "brand": "ROADMASTER"
        }
        """
        # fist call to assign `self.additional_json`
        json_data = self.get_additional_json()
        return json_data.get('productBasicInfo', {})

    def get_products(self):
        """
        return all product dicts

        "products": {
          "758OE1KHM2DC": {
            "usItemId": "710460253",
            "productId": "758OE1KHM2DC",
            "offers": [
              "8348CF7A0C0A4E9FA4E8E0FECEF541C5"
            ],
            "images": [
              "5C6FD954208446A4A9840D4FE37F2FEC",
              "FD3D07398D6B48C093F439CAD644393F"
            ],
          }, ....
        }
        """
        return self.additional_json.get('product', {}).get('products', {})

    def find_price(self, price):
        price = str(price).replace(',', '') if price else ''
        match = re.search(r'[0-9.]+', price)
        if match:
            price = match.group()
        return float(price) if price else None

    # ----------------------------
    # BEGIN OF ABSTRACT FUNCTIONS
    # ----------------------------

    def get_product_code(self):
        """
        function to get product code of product
        :return string code of product.
        """
        product_info = self.get_product_info()
        return product_info.get('selectedProductId')

    def get_product_id(self):
        """
        function to get product id of product
        :return string id of product.
        """
        product_info = self.get_product_info()
        product_code = product_info.get('selectedProductId')
        return product_info.get(product_code, {}).get('usItemId')

    def get_name(self, field_name='NAME'):
        """
        function to get name/title of product
        :return string name of product.
        """
        product_info = self.get_product_info()
        product_id = product_info.get('selectedProductId')
        product_title = None
        if product_id:
            product_title = product_info.get(product_id, {}).get('title')
        return product_title or self.get_default(field_name)

    def get_country(self):
        """
        function to get product/item location.
        :return string of country
        """
        pass

    def get_prices(self, field_name='PRICE'):
        """
        function to get prices of product.
        :return list prices of product.
        """
        # `maxPrice` dan `minPrice` ternyata tidak bisa dijadikan acuan,
        # karena ada kalanya `maxPrice` & `minPrice` berisi 0, padahal pricenya ada.
        #
        # product_code = self.get_product_code()
        # product = self.additional_json.get('sellersHeading', {}).get(product_code, {})
        # max = product.get('maxPrice', 0)
        # min = product.get('minPrice', 0)
        # if (min > 0) and (max > 0):
        #     return [min, max] if min != max else [max]
        #
        # midas = self.additional_json.get('product', {}).get('midasContext', {})
        # if midas.get('price', 0) > 0:
        #     return [midas.get('price', 0)]
        # return []

        field, data = field_name, eval(field_name)
        raw = self.scrap(field=field, data=data)
        prices = []
        if isinstance(raw['value'], list):
            for price in raw['value']:
                prices.append(self.find_price(price))
        return prices

    def get_price(self):
        """
        function to get fixed price of product.
        :return float (eg: 29.83) or None
        """
        prices = self.get_prices()
        return max(prices) if len(prices) > 0 else None

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

    def get_currency_code(self, field_name='CURRENCY_CODE'):
        """
        function to get the price code, eg: IDR, USD, DBP, etc.
        :return string of price code
        """
        return self.get_default(field_name)

    def get_currency_value(self):
        """
        function to get converted money from eg: 1 USD to IDR
        :return float of currency value or None
        """
        currency_code = self.get_currency_code()
        if currency_code:
            return currency(1, from_money=currency_code, to_money='IDR')
        return None

    def get_category(self, field_name='CATEGORY'):
        """
        function to get category of product.
        :return string of category
        """
        field, data = field_name, eval(field_name)
        raw = self.scrap(field=field, data=data)
        if raw['method'] == None:
            return raw['value']
        return ', '.join(raw['value']) if raw else None

    def get_availability(self):
        """
        function to get product availability
        :return string/text of product availability.
        """
        product_offers = self.additional_json.get('product', {}).get('offers', {})
        for key, value in product_offers.items():
            if type(value) is dict:
                product_code = self.get_product_code()
                if value.get('productId') == product_code:
                    return value.get('productAvailability', {}).get('availabilityStatus')
        return ''

    def get_image_urls(self):
        """
        function to get all thumbnail image urls of product.
        :return list urls of images.
        """
        products = self.get_products()

        def get_image_keys():
            """
            "images": [
              "5C6FD954208446A4A9840D4FE37F2FEC",
              "FD3D07398D6B48C093F439CAD644393F"
            ]
            """
            for code, value in products.items():
                if code == self.get_product_code():
                    return value.get('images', [])
            return []

        image_keys = get_image_keys()
        product_images = self.additional_json.get('product', {}).get('images', {})
        product_images_list = []

        for key, image in product_images.items():
            if key in image_keys:
                if type(image) is dict:
                    image_url = image.get('assetSizeUrls', {}).get('main')
                    if image_url:
                        product_images_list.append(image_url)
        return product_images_list

    def get_image_url(self):
        """
        function to get fist thumbnail image of product.
        :return string url of image
        """
        product_info = self.get_product_info()
        product_id = product_info.get('selectedProductId')
        if product_id:
            image_url = product_info.get(product_id, {}).get('imageUrl')
            if image_url:
                return str(image_url).split('?')[0]

        image_urls = self.get_image_urls()
        if len(image_urls) > 0:
            return image_urls[0]
        return None

    def get_description(self):
        """
        function to get description html of product.
        :return html string of product description.
        """
        product_code = self.get_product_code()
        map = self.additional_json.get('product', {}).get('idmlMap', {})
        long_desc = map.get(product_code, {}).get('modules', {}).get('LongDescription', {})
        return '<br />'.join(long_desc.get('product_long_description', {}).get('values', []))

    def get_max_quantity(self):
        """
        function to get maximum quantity of product.
        :return integer or None
        """
        product_offers = self.additional_json.get('product', {}).get('offers', {})
        for key, value in product_offers.items():
            if type(value) is dict:
                product_code = self.get_product_code()
                if value.get('productId') == product_code:
                    options = value.get('offerInfo', {}).get('quantityOptions', {})
                    return options.get('orderLimit')
        return None

    def get_weight(self):
        """
        function to get weight of product
        :return integer or float
        """
        # FIXME: BELUM ADA KEPUTUSAN
        return 0

    def get_weight_unit(self):
        """
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
        return 'walmart.com'  # default fot this class.WalmartScraper

    def get_options(self):
        """
        function to get options menu (product selection)
        :result `choices` is a dict {} in this `walmart.py`
        :return list of selection type

        result of this options is look like this:
        [
          {
            "specification_key": "colour_men",
            "specification": "Colour Men",
            "choices": [
                {"name": "Black", "key": "black", "url": "https://foobar.com", "selected": false},
                {"name": "One Wash", "key": "one_wash", "url": "https://baz.com", "selected": true}
            ]
          },
          ....
        ]
        """
        product_code = self.get_product_code()
        product_categories = self.additional_json.get('product', {})\
            .get('variantCategoriesMap', {})
        product_options = []

        for key, value in product_categories.items():
            if type(value) is dict:
                for label, varian in value.items():
                    if type(varian) is dict:
                        # 1. without urls, type `choices` is a list of strings
                        # choices_list = []
                        # choices = varian.get('variants', {})
                        # for k, v in choices.items():
                        #     if type(v) is dict:
                        #         choices_list.append(v.get('name'))
                        #
                        # choices_list = list(set(choices_list))
                        # product_options.append({
                        #     'specification_key': varian.get('id'),
                        #     'specification': varian.get('name'),
                        #     'choices': choices_list
                        # })

                        # 2. with urls, type `choices` is a list of dicts
                        def get_product_url(product_codes):
                            if len(product_codes) > 0:
                                product_code = product_codes[0]
                                for code, val in self.get_products().items():
                                    if code == product_code:
                                        product_id = val.get('usItemId')
                                        product_url = 'https://www.walmart.com/ip/%s?selected=true' % product_id
                                        return product_url if product_id else None
                            return None

                        choices_list = []
                        choices = varian.get('variants', {})
                        selected_value = None

                        for k, v in choices.items():
                            if type(v) is dict:
                                product_url = get_product_url(v.get('products', []))
                                choices_list.append({
                                    "key": v.get('id'),
                                    "name": v.get('name'),
                                    "url": product_url,
                                    "selected": v.get('selected', False)
                                })
                                if v.get('selected'):
                                    selected_value = v.get('name')

                        product_options.append({
                            'specification_key': varian.get('id'),
                            'specification': varian.get('name'),
                            'choices': choices_list,
                            'selected': selected_value
                        })

        return product_options

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

    def get_page_mode(self):
        """
        function to differentiate the page mode,
        for example:
            - amazon scraper using 'reload'
            - ebay scraper using 'combination'

        :return string of 'combination', 'reload' or etc.
        """
        return 'reload'


if __name__ == '__main__':
    try:
        url = 'https://www.walmart.com/ip/V-Neck-Merino-Wool-Sweater/622635302'
        if len(sys.argv) > 1:
            url = sys.argv[-1]

        raw_response = ScrapRequest().get(url)
        scraper = WalmartScraper(url, raw_response)
        response = scraper.get_result()
    except Exception as error:
        response = {'action': False, 'error_message': str(error)}

    print(response)

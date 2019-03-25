# -*- coding: utf-8 -*-

import json
import datetime
import traceback

from abc import (ABC, abstractmethod)


class Scraper(ABC):
    """
    abstract class for global Scrapers

    [i] if you got this an error:
        "TypeError: Can't instantiate abstract class Amazon with abstract methods get_name"
        you should create the function `get_name` inside instance class.

    [i] e.g usage:

    class EbayScraper(Scraper):

        def __init__(self, url, raw_response):
            self.url = url
            self.page_text = None
            self.page_content = None
            self.html_content = None

            if raw_response['status_code'] == 200:
                self.page_text = raw_response['content'].text
                self.page_content = raw_response['content'].content
                self.html_content = html.fromstring(self.page_content)

            # initialize from parent to fetch `self.RESPONSE_DATA`
            super().__init__(url)

        def get_name(self):
            return 'hello'

        def get_product_id(self):
            return '7HDA97'
    """

    def __init__(self, url):
        self.url = url                     # url of product
        self.RESPONSE_DATA = {
            'NAME': '',                    # name of product
            'PRODUCT_ID': '',              # product code/id
            'PRODUCT_CODE': '',            # product code/id
            'COUNTRY': '',                 # product location
            'PRICE': None,                 # product price
            'PRICES': [],                  # product prices
            'PRICE_DOLLAR': None,          # dollar value, eg: 0.531 from CNY to USD (float)
            'CURRENCY_CODE': '',           # currency code (USD, GBP, IDR, etc)
            'CURRENCY_VALUE': None,        # currency value, eg: 1 USD to IDR
            'CATEGORY': '',                # category of product
            'AVAILABILITY': '',            # product availability
            'URL': '',                     # original product url
            'IMAGE_URL': '',               # product image url
            'IMAGE_URLS': [],              # product image urls
            'DESCRIPTION': '',             # description of product
            'MAX_QUANTITY': None,          # if it has maximum quantity (integer)
            'WEIGHT': 0,                   # weight of product
            'WEIGHT_UNIT': 'gram',         # weight unit of product
            'SHIPPING_WEIGHT': None,       # shipping weight of product
            'DIMENSION': [],               # for amazon & tmall
            'DIMENSION_HEIGHT': None,      # dimension height of product
            'DIMENSION_WIDTH': None,       # dimension width of product
            'DIMENSION_LENGTH': None,      # dimension length of product
            'DIMENSION_UNIT': 'cm',        # dimension unit of product
            'MARKETPLACE': '',             # coming from? 'amazon.com', 'ebay.com', etc
            'VARIATIONS': [],              # eg: [{"Size": "XL", "price": 2.89, "Colour": "Black"}]
            'OPTIONS': [],                 # eg: [{"specification": "Size", "choices": ["S", "M"]}]
            'PAGE_MODE': 'combination',    # eg: 'combination', 'reload' or etc.
            'action': False,               # to makesure that scrap is success or not.
            'FLAG': None                   # to add additional flag, eg: 'bid', etc.
        }

    def __repr__(self):
        return '%s(url="%s")' % (self.__class__.__name__, self.url)

    @abstractmethod
    def get_name(self):
        """
        function to get name/title of product
        :return string name of product.
        """
        pass

    @abstractmethod
    def get_product_id(self):
        """
        function to get product id of product
        :return string id of product.
        """
        pass

    @abstractmethod
    def get_product_code(self):
        """
        function to get product code of product
        :return string code of product.
        """
        pass

    @abstractmethod
    def get_country(self):
        """
        function to get product/item location.
        :return string of country
        """
        pass

    @abstractmethod
    def get_price(self):
        """
        function to get fixed price of product.
        :return float (eg: 29.83) or None
        """
        pass

    @abstractmethod
    def get_prices(self):
        """
        function to get prices of product.
        :return list prices of product.
        """
        pass

    @abstractmethod
    def get_price_dollar(self):
        """
        function to convert the product price into dollar.
        eg: from CNY to USD
        :return float(eg: 29.83) or None
        """
        pass

    @abstractmethod
    def get_currency_code(self):
        """
        function to get the price code, eg: IDR, USD, DBP, etc.
        :return string of price code
        """
        pass

    @abstractmethod
    def get_currency_value(self):
        """
        function to get converted money from eg: 1 USD to IDR
        :return float of currency value or None
        """
        pass

    @abstractmethod
    def get_category(self):
        """
        function to get category of product.
        :return string of category
        """
        pass

    @abstractmethod
    def get_availability(self):
        """
        function to get product availability
        :return string/text of product availability.
        """
        pass

    @abstractmethod
    def get_image_url(self):
        """
        function to get fist thumbnail image of product.
        :return string url of image
        """
        pass

    @abstractmethod
    def get_image_urls(self):
        """
        function to get all thumbnail image urls of product.
        :return list urls of images.
        """
        pass

    @abstractmethod
    def get_description(self):
        """
        function to get description html of product.
        :return html string of product description.
        """
        pass

    @abstractmethod
    def get_max_quantity(self):
        """
        function to get maximum quantity of product.
        :return integer or None
        """
        pass

    @abstractmethod
    def get_weight(self):
        """
        function to get weight of product
        :return integer or float
        """
        pass

    @abstractmethod
    def get_weight_unit(self):
        """
        function to get weight unit, eg: 'gram', 'kg', 'pounds'
        :return string of weight unit, default 'gram'
        """
        pass

    @abstractmethod
    def get_shipping_weight(self):
        """
        function to get shipping weight if it exist.
        :return integer, float or None
        """
        pass

    @abstractmethod
    def get_dimension_height(self):
        """
        function to get dimension height if it exist.
        :return integer, float or None
        """
        pass

    @abstractmethod
    def get_dimension_width(self):
        """
        function to get dimension width if it exist.
        :return integer, float or None
        """
        pass

    @abstractmethod
    def get_dimension_length(self):
        """
        function to get dimension length if it exist.
        :return integer, float or None
        """
        pass

    @abstractmethod
    def get_dimension_unit(self):
        """
        function to get dimension unit of product, eg: 'cm', 'm'
        :return string of dimension unit, default 'cm'
        """
        pass

    @abstractmethod
    def get_marketplace(self):
        """
        function to get the name of marketplace, eg: 'amazon.com', 'ebay.com'
        :return string name of marketplace
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_page_mode(self):
        """
        function to differentiate the page mode,
        for example:
            - amazon scraper using 'reload'
            - ebay scraper using 'combination'

        :return string of 'combination', 'reload' or etc.
        """
        pass

    def get_flag(self):
        """
        manual flag to identify specific product
        :return string, eg: 'bid'
        """
        pass

    def get_result(self):
        """
        return dict of `self.RESPONSE_DATA` without saving into database.
        """
        try:
            self.RESPONSE_DATA['NAME'] = self.get_name()
            self.RESPONSE_DATA['PRODUCT_ID'] = self.get_product_id()
            self.RESPONSE_DATA['PRODUCT_CODE'] = self.get_product_code()
            self.RESPONSE_DATA['COUNTRY'] = self.get_country()
            self.RESPONSE_DATA['PRICE'] = self.get_price()
            self.RESPONSE_DATA['PRICES'] = self.get_prices()
            self.RESPONSE_DATA['PRICE_DOLLAR'] = self.get_price_dollar()
            self.RESPONSE_DATA['CURRENCY_CODE'] = self.get_currency_code()
            self.RESPONSE_DATA['CURRENCY_VALUE'] = self.get_currency_value()
            self.RESPONSE_DATA['CATEGORY'] = self.get_category()
            self.RESPONSE_DATA['AVAILABILITY'] = self.get_availability()
            self.RESPONSE_DATA['URL'] = self.url
            self.RESPONSE_DATA['IMAGE_URL'] = self.get_image_url()
            self.RESPONSE_DATA['IMAGE_URLS'] = self.get_image_urls()
            self.RESPONSE_DATA['DESCRIPTION'] = self.get_description()
            self.RESPONSE_DATA['MAX_QUANTITY'] = self.get_max_quantity()
            self.RESPONSE_DATA['WEIGHT'] = self.get_weight()
            self.RESPONSE_DATA['WEIGHT_UNIT'] = self.get_weight_unit()
            self.RESPONSE_DATA['SHIPPING_WEIGHT'] = self.get_shipping_weight()
            self.RESPONSE_DATA['DIMENSION_HEIGHT'] = self.get_dimension_height()
            self.RESPONSE_DATA['DIMENSION_WIDTH'] = self.get_dimension_width()
            self.RESPONSE_DATA['DIMENSION_LENGTH'] = self.get_dimension_length()
            self.RESPONSE_DATA['DIMENSION_UNIT'] = self.get_dimension_unit()
            self.RESPONSE_DATA['MARKETPLACE'] = self.get_marketplace()
            self.RESPONSE_DATA['VARIATIONS'] = self.get_variations()
            self.RESPONSE_DATA['OPTIONS'] = self.get_options()
            self.RESPONSE_DATA['PAGE_MODE'] = self.get_page_mode()
            self.RESPONSE_DATA['FLAG'] = self.get_flag()
            self.RESPONSE_DATA['action'] = True
            return self.RESPONSE_DATA
        except Exception:
            error = traceback.format_exc()
            return {'action': False, 'error_message': str(error)}

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


NAME = {'xpath': ['//span[@id="vi-lkhdr-itmTitl"]//text()']}
PRODUCT_ID = {'xpath': ['//div[@id="descItemNumber"]//text()']}
COUNTRY = {'xpath': ['//span[@itemprop="availableAtOrFrom"]//text()']}
CATEGORY = {'xpath': ['//li[@class="bc-w"]/a//text()']}
PRICES = {'xpath': ['//span[@id="prcIsum"]//text()', '//span[@id="mm-saleDscPrc"]']}
ORIGINAL_PRICE = {'xpath': ['//span[@id="orgPrc"]//text()', '//span[@id="mm-saleOrgPrc"]//text()']}
AVAILABILITY = {'xpath': ['//span[@id="qtySubTxt"]//text()',  # More than 10 available, Limited quantity available
                          '//span[@id="qtySubTxt"]/span//text()']}
DESCRIPTION = {'xpath': ['//div[@id="desc_div"]']}
IMAGE_URLS = {'xpath': ['//div[@id="vi_main_img_fs"]']}
IMAGE_URL = {'xpath': ['//img[@id="icImg"]/@src']}


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

    def __repr__(self):
        return '%s(url="%s")' % (self.__class__.__name__, self.url)

    def use_x_path(self, path):
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
        parse the javascript variables into dict format.
        eg:
            {
              'ActionPanel': {},
              'ItemVariations': {},
              'PicturePanel': {}
            }
        """
        EBAY_DATA = {
            'action': False,
            'ActionPanel': {},
            'ItemVariations': {},
            'PicturePanel': {}
        }
        if self.html_content is not None:
            try:
                query = "//script[contains(text(), 'ebay.context.Context')]/text()"
                script = self.html_content.xpath(query)
                script_js = script[0].replace('\n', '').replace('\r', '').replace('\t', '')

                # 1. ActionPanel
                def get_action_panel():
                    script_regex = r'raptor.vi.ActionPanel\S+\{\"?[.*]*(.*)\,\"liveAuctionHidePayNow\"'
                    matches = re.finditer(script_regex, script_js, re.MULTILINE)

                    try:
                        for numb, match in enumerate(matches):
                            groups = match.groups()
                            if len(groups) > 0:
                                script_to_eval = 'var ActionPanel = {"' + groups[0] + '}}'
                                script_data = js2py.eval_js(script_to_eval)
                                if not isinstance(script_data, dict):
                                    return script_data.to_dict()
                                return script_data
                    except Exception:
                        error = traceback.format_exc()
                        capture_exception(error)
                    return {}

                # 2. ItemVariations
                def get_item_variations():
                    script_regex = "com.ebay.raptor.vi.msku.ItemVariations\S+\{\"?[.*]*(.*)],\['com.ebay.raptor.vi.isum.smartBackTo"
                    matches = re.finditer(script_regex, script_js, re.MULTILINE)

                    try:
                        for numb, match in enumerate(matches):
                            groups = match.groups()
                            if len(groups) > 0:
                                script_to_eval = 'var ItemVariations = {"' + groups[0]
                                script_data = js2py.eval_js(script_to_eval)
                                if not isinstance(script_data, dict):
                                    return script_data.to_dict()
                                return script_data
                    except Exception as error:
                        pass  # IndexError
                    return {}

                # 3. PicturePanel
                def get_picture_panel():
                    # script_regex = 'ebay.viewItem.PicturePanelPH\S+\{\"?[.*]*(.*)\);var notification'
                    script_regex = 'ebay.viewItem.PicturePanelPH\S+\(\{\+?[.*]*(.*)\}\]\}\);'
                    matches = re.finditer(script_regex, script_js, re.MULTILINE)

                    try:
                        for numb, match in enumerate(matches):
                            groups = match.groups()
                            if len(groups) > 0:
                                script_to_eval = 'var PicturePanel = {' + groups[0] + '}]}'
                                script_data = js2py.eval_js(script_to_eval)
                                if not isinstance(script_data, dict):
                                    return script_data.to_dict()
                                return script_data
                    except Exception:
                        error = traceback.format_exc()
                        capture_exception(error)
                    return {}

                EBAY_DATA['action'] = True
                EBAY_DATA['ActionPanel'] = get_action_panel() or {}
                EBAY_DATA['ItemVariations'] = get_item_variations() or {}
                EBAY_DATA['PicturePanel'] = get_picture_panel() or {}

            except IndexError:
                pass  # noqa

            except Exception:
                error = traceback.format_exc()
                capture_exception(error)

        return EBAY_DATA

    def get_additional_data(self):
        """
        function to get additional data for field_name `ADDITIONAL`
        :return a dict of {'DIMENSION': [], 'DIMENSION_TEXT': [], ...}
        """
        additional_json = self.get_additional_json()
        additional_data = {
            'DIMENSIONS': [],
            'DIMENSION_TEXT': [],
            'PRODUCT_ID': '',
            'PRODUCT_CODE': '',
            'SELECTED_INDEX': {},
            'SELECTED_VALUES': {},
            'DIMENSION_VALUES': {},
            'COMBINATIONS': '',
            'DIMENSIONS_STATUS': '',
            'ASINMAP': '',
            'ASIN_VARIATIONS': {},
            'MENU_ITEM_MAPS': {},
            'SPECIFICATIONS_DATA': []
        }

        def get_dimensions(is_key=True, track_menu=False):
            """
            is_key=False
                ['Size', 'Color', 'Macam macam']

            is_key=True
                ['size', 'color', 'macam_macam']

            track_menu=True
                {'size': [1, 2, 3, 4], 'color': [5, 6, 7]}
            """
            try:
                dimensions = additional_json['ItemVariations']['itmVarModel']['menuModels']
            except Exception:
                dimensions = []

            dimensions_dict = {}
            dimensions_list = []

            for menu in dimensions:
                dimension = menu.get('displayName', '')
                dimension = dimension.replace(' ', '_').lower() if is_key else dimension

                if track_menu == True:
                    dimensions_dict[dimension] = menu.get('menuItemValueIds')
                else:
                    dimensions_list.append(dimension)

            if track_menu:
                return dimensions_dict
            return dimensions_list

        def get_selected_index():
            """
            {'color': -1, 'macam_macam': -1, 'size': -1}
            """
            dimension_keys = get_dimensions(is_key=True)
            return dict(zip(dimension_keys, [-1] * len(dimension_keys)))

        def get_dimension_values():
            """
            Output of this dimension values:
                {'waist_size':['W28','W30', ...],
                 'leg_length':['L30','L32', ...],
                 'colour':['Black','Light Broken-In', ...]}
            """
            # {'size': [1, 2, 3, 4], 'color': [5, 6, 7]}
            dimension_menus = get_dimensions(is_key=True, track_menu=True)

            try:
                # this below line is <class 'js2py.base.JsObjectWrapper'> or dict
                dimension_maps = additional_json['ItemVariations']['itmVarModel']['menuItemMap']
                if not isinstance(dimension_maps, dict):
                    dimension_maps = dimension_maps.to_dict()
            except Exception:
                dimension_maps = {}

            dimension_maps_out = {}
            for key, values in dimension_menus.items():
                new_values = []
                for number in values:
                    name = dimension_maps.get(str(number))
                    if name is not None:
                        name = name.get('displayName')
                        new_values.append(name)
                dimension_maps_out.update({key: new_values})
            return dimension_maps_out

        def get_asin_variations():
            """
            Output of this asin variations:
                {
                  "3123970990755": {
                    "size": "5",
                    "colour": "2",
                    "ASIN": "3123970990755"
                  },
                  "3123970990765": {
                    "size": "6",
                    "colour": "2",
                    "ASIN": "3123970990765"
                  }
                }
            """
            try:
                # this below line is <class 'js2py.base.JsObjectWrapper'> or dict
                variation_maps = additional_json['ItemVariations']['itmVarModel']['itemVariationsMap']
                if not isinstance(variation_maps, dict):
                    variation_maps = variation_maps.to_dict()
            except Exception:
                variation_maps = {}

            variation_maps_out = {}
            for key, val in variation_maps.items():
                val = val if type(val) is dict else {}
                val['ASIN'] = key

                # actually this index is already on ['610651942238']['traitValuesMap']
                for dimension, index_menu in val.get('traitValuesMap', {}).items():
                    dimension = dimension.replace(' ', '_').lower()
                    index_menu = str(index_menu) if type(index_menu) is int else index_menu
                    val[dimension] = index_menu

                dimensions_dict = {key: val}
                variation_maps_out.update(**dimensions_dict)

            return variation_maps_out

        def get_menu_item_maps():
            """
            Output of this menu item maps:
            {
              "14": {
                "displayName": "W44",
                "valueId": 14,
              }
            }
            """
            try:
                # this below line is <class 'js2py.base.JsObjectWrapper'> or dict
                menu_item_maps = additional_json['ItemVariations']['itmVarModel']['menuItemMap']
                if not isinstance(menu_item_maps, dict):
                    menu_item_maps = menu_item_maps.to_dict()
            except Exception:
                menu_item_maps = {}
            return menu_item_maps

        additional_data['DIMENSIONS'] = get_dimensions(is_key=True)
        additional_data['DIMENSION_TEXT'] = get_dimensions(is_key=False)
        additional_data['PRODUCT_ID'] = ''
        additional_data['PRODUCT_CODE'] = ''
        additional_data['SELECTED_INDEX'] = get_selected_index()
        additional_data['SELECTED_VALUES'] = {}  # kosong karena selected index -1
        additional_data['DIMENSION_VALUES'] = get_dimension_values()
        additional_data['COMBINATIONS'] = ''
        additional_data['DIMENSIONS_STATUS'] = ''
        additional_data['ASINMAP'] = ''
        additional_data['ASIN_VARIATIONS'] = get_asin_variations()
        additional_data['MENU_ITEM_MAPS'] = get_menu_item_maps()
        additional_data['SPECIFICATIONS_DATA'] = []

        return additional_data

    def get_extract_image_urls(self, is_first=False):
        """
        function to get image url/s of product.

        :param `is_first` (boolean) use to get first image or not.
        :return image url/s, which type data as list, string, or null(None)
                list   => ['https://.../foobar.jpg', 'https://.../baz.jpg']
                string => 'https://.../foobar.jpg'
                null   => None
        """
        additional_json = self.get_additional_json()
        image_urls = []

        try:
            image_list = additional_json['PicturePanel']['fsImgList']
        except Exception:
            image_list = []

        for image in image_list:
            image_urls.append(image.get('displayImgUrl'))

        image_urls = list(set(image_urls))
        if len(image_urls) < 1:
            try:
                raw = self.scrap(field='IMAGE_URL', data=IMAGE_URL)
                image_urls = list(set(raw['value']))
            except Exception:
                pass

        if is_first == True:
            return image_urls[0] if len(image_urls) > 0 else None
        return image_urls

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
        default = self.get_default(field_name)
        if default != '' and default != None:
            return '%s' % str(default).split(',')[-1].strip()
        return ''

    def get_price_data(self):
        """
        function to get fix price,
        after getting a discount, coupon, or etc.

        :return dict of price:
            {'price: <float>, 'code': <string>, 'flag': <string>}
            {'price': 831.41, 'code': 'USD', 'flag': 'bid'}
        """
        additional_json = self.get_additional_json()
        price_data = {'price': None, 'code': None, 'flag': None}

        try:
            model = additional_json.get('ActionPanel', {}).get('isModel', {})
            price_data['code'] = model.get('currencyCode')

            if model.get('bid'):
                price_data['flag'] = 'bid'
                price_data['price'] = self.find_price(model.get('bidPrice'))
            else:
                price_data['price'] = self.find_price(model.get('binPriceOnly'))

        except Exception:
            error = traceback.format_exc()
            capture_exception(error)

        return price_data

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
        :return string of category
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
        function to get dimension width if it exist.
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
        return 'ebay.com'  # default for this class.EbayScraper

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
        additional_data = self.get_additional_data()
        variations_out = []

        for key, value in additional_data['ASIN_VARIATIONS'].items():
            # only add `quantityAvailable` > 0
            quantity_available = value.get('quantityAvailable', 0)

            if quantity_available > 0 and type(value) is dict:
                # output of this `variation` below should be:
                # {"colour": 1, "leg_length": 16, "ASIN": "610725556127", "waist_size": 4, "quantity_available": 1}
                variation = {'ASIN': key, 'quantity_available': quantity_available}

                price = value.get('priceAmountValue', {}).get('convertedFromValue', None)
                variation.update({'price': price, 'currency_code': self.get_currency_code()})
                # print(variation)
                # {'price': 49.9, 'ASIN': '610441601768', 'currency_code': 'USD'}

                variation_maps = value.get('traitValuesMap', {})
                # print(variation_maps)
                # {'Colour': 2, 'Waist Size': 11, 'Leg Length': 18}

                try:
                    menu_item_maps = additional_data['MENU_ITEM_MAPS']
                    for new_label, index in variation_maps.items():
                        # without key
                        new_value = menu_item_maps.get(str(index), {}).get('displayName')
                        variation.update({new_label: new_value})

                        # with key
                        new_label_key = new_label.replace(' ', '_').lower()
                        variation.update({new_label_key: new_value})
                except Exception as error:
                    pass

                # to makesure that `price` isn't None
                if variation.get('price'):
                    variations_out.append(variation)

        return variations_out

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

    def get_flag(self):
        """
        additional flag, if the product indentified as 'bid'
        """
        price_data = self.get_price_data()
        if price_data.get('flag'):
            return price_data.get('flag')
        return None


if __name__ == '__main__':
    try:
        url = 'https://www.ebay.com/itm/192542735939'
        if len(sys.argv) > 1:
            url = sys.argv[-1]

        raw_response = ScrapRequest().get(url)
        scraper = EbayScraper(url, raw_response)
        response = scraper.get_result()
    except Exception as error:
        response = {'action': False, 'error_message': str(error)}

    print(response)

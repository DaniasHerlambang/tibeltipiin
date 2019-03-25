
#### Run in environtment

> Install python virtual environtment firs, checkout [at this link](https://www.pythonforbeginners.com/basics/how-to-use-python-virtualenv).

```
$ virtualenv --python=/usr/bin/python3.5 env-kp-titipbeliin
$ cd env-kp-titipbeliin
$ source bin/activate
$ git clone https://gitlab.com/titipbeliin/kp-titipbeliin.git
$ cd kp-titipbeliin
```

#### Install requirements

```
pip install -r requirements.txt
```

#### Update the proxy

```
python scraper/utils/upproxy.py
```


#### Test Scraper

```
python scraper/walmart.py https://www.walmart.com/ip/V-Neck-Merino-Wool-Sweater/622635302   (ada variasinya, tapi tidak ada kombinasi harganya)

python scraper/ebay.py https://www.ebay.com/itm/192542735939                                (ada variasinya & kombinasi harganya)
```

> Contoh output harus mengacu pada file:
> `results/ebay.py.js` atau `results/walmart.py.js`

> Analisa setiap situs yg akan discrap, apakah dia memiliki variasi & kombinasi harga ataukah tidak.
> Seperti contoh pada `ebay.com` _(yang memiliki variasi & kombinasi harga)_ di masing-masing variasi produk yg dipilih,
> contoh: kombinasi warna hitam + size xl harganya $20, sedangkan warna hitam + size l: harganya $19.
> Variasi tersebut tidak berlaku seperti pada situs `walmart.com` karena setiap dipilih variasinya, dia reload ke variasi ID yang dipilih untuk mendapatkan harga dari variasi produk.
> Sehingga model seperti ini mengacu pada:


```
'OPTIONS': [
  {
    'specification': 'Clothing Size',
    'specification_key': 'clothing_size',
    'choices': [
      {
        'key': 'clothing_size-medium',
        'name': 'Medium',
        'selected': False,
        'url': 'https://www.walmart.com/ip/654025362?selected=true'            # ada field tambahan berupa url & selected=True/False
      },
      ...
    ]
  }
]
```

Berbeda dengan `ebay.com` yang memiliki variasi & kombinasi harga:

```
'OPTIONS': [
  {
    'choices': [
      'For iPhone 6',
      'For iPhone 6s',
      'For iPhone 6 Plus',
      'For iPhone 6s Plus',
      'For iPhone 7',
      'For iPhone 8',
      'For iPhone 7 Plus',
      'For iPhone 8 Plus',
      'For iPhone X',
      'For iPhone  6 Plus',
      'For iPhone XS',
      'For iPhone XS MAX',
      'For iPhone XR'
    ],
    'specification': 'To Fit For Model',
    'specification_key': 'to_fit_for_model'
  },
```

Bagian `OPTIONS` diatas digunakan nantinya untuk pencarian `VARIATIONS`, dengan mengacu pada
`specification` dan `specification_key` dengan value-nya adalah `choices` yang dipilih oleh user.

```
'VARIATIONS': [
  {
    'price': 5.99,
    'quantity_available': 1,
    'color': 'Red',
    'ASIN': '492797672433',
    'To fit for model': 'For iPhone XS',
    'to_fit_for_model': 'For iPhone XS',
    'currency_code': 'USD',
    'Color': 'Red'
  },
```

---------------------------

#### Table Marketplaces

No  | Website                             | Country | Done                        |
----|-------------------------------------|---------|-----------------------------|
1   | https://www.rakuten.com             | Japan   | :white\_check\_mark:        |
2   | https://www.amazon.co.jp            | Japan   | :white\_check\_mark:        |
3   | https://www.kakaku.com              | Japan   |                             |
4   | https://www.gmarket.co.kr           | Korea   | :arrows\_counterclockwise:  |
5   | https://www.qoo10.com               | Korea   |                             |
6   | http://www.11st.co.kr               | Korea   |                             |
7   | https://www.daimaru-matsuzakaya.jp  | Japan   |                             |
8   | http://www.1688.com                 | China   | :arrows\_counterclockwise:  |
9   | http://www.tmall.com                | China   | :white\_check\_mark:        |
10  | http://www.aliexpress.com           | China   | :white\_check\_mark:        |
11  | http://www.wemakeprice.com          | Korea   |                             |
12  | https://www.coupang.com             | Korea   | :arrows\_counterclockwise:  |
13  | http://www.taobao.com               | China   | :white\_check\_mark:        |
14  | http://www.360buy.com               | China   | :no\_entry\_sign:           |
15  | http://www.ju.taobao.com            | China   | :no\_entry\_sign:           |
16  | http://www.yihaodian.com (yhd.com)  | China   |                             |
17  | https://www.jd.com                  | China   |                             |
18  | http://www.vancl.com                | China   |                             |
19  | http://www.dangdang.com             | China   |                             |
20  | http://www.walmart.com              | US      | :white\_check\_mark:        |
21  | http://www.bestbuy.com              | US      |                             |
22  | http://www.amazon.com               | US      | :white\_check\_mark:        |
23  | http://www.ebay.com                 | US      | :white\_check\_mark:        |
24  | https://www.alibaba.com             | China   |                             |

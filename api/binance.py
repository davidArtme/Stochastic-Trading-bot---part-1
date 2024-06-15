import hashlib
import hmac
import time
import requests


class Binance_api:
    spot_link = "https://api.binance.com"
    futures_link = "https://fapi.binance.com"

    def __init__(self, api_key=None, secret_key=None, futures=False,
                 proxy_ip=None, proxy_port=None,
                 proxy_username=None, proxy_password=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.futures = futures
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.base_link = self.futures_link if self.futures else self.spot_link
        self.header = {'X-MBX-APIKEY': self.api_key}
        if self.proxy_ip:
            self.proxies = {
                "http": f"http://{self.proxy_username}:{self.proxy_password}@{self.proxy_ip}:{self.proxy_port}",
                "https": f"http://{self.proxy_username}:{self.proxy_password}@{self.proxy_ip}:{self.proxy_port}",
            }
        else:
            self.proxies = None

    def gen_signature(self, params):
        param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
        sign = hmac.new(bytes(self.secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256).hexdigest()
        return sign

    def http_request(self, method, endpoint, params=None, sign_need=False):
        """
        Отправляет http запрос на сервер торговой площадки

        :param endpoint: url адрес запроса
        :param method: тип запроса (GET, POST, DELETE)
        :param params: тело запроса (params)
        :param sign_need: проверка если нужно подставить подпись

        :return: :class:Response (requests.models.Response)
        """

        if params is None:
            params = {}

        # Добавляем в словарь, если необходимо, параметры для подписи - отпечаток времени и саму подпись.
        if sign_need:
            params['timestamp'] = int(time.time() * 1000)

            params['signature'] = self.gen_signature(params)

        url = self.base_link + endpoint
        if method == "GET":
            response = requests.get(url=url, params=params, headers=self.header, proxies=self.proxies)
        elif method == "POST":
            response = requests.post(url=url, params=params, headers=self.header, proxies=self.proxies)
        elif method == "DELETE":
            response = requests.delete(url=url, params=params, headers=self.header, proxies=self.proxies)
        else:
            return print("Метод не известен!")
        if response:  # Проверяем если ответ не пустой - чтоб не получить ошибки форматирования пустого ответа.
            response = response.json()
        else:
            print(response.text)
        return response

    def get_price_ticker(self, symbol: str = None):
        if self.futures:
            endpoint = "/fapi/v1/ticker/price"
        else:
            endpoint = "/api/v3/ticker/price"
        method = "GET"
        params = {}
        if symbol:
            params['symbol'] = symbol

        return self.http_request(method=method, endpoint=endpoint, params=params)



    def get_exchange_info(self, symbol=None, symbols=None):
        if self.futures:
            endpoint = '/fapi/v1/exchangeInfo'
        else:
            endpoint = '/api/v3/exchangeInfo'
        method = "GET"
        params = {}
        if symbol and not symbols:
            params['symbol'] = symbol
            return self.http_request(endpoint=endpoint, method=method, params=params)

        if symbols and not symbol:
            params['symbols'] = symbols
            return self.http_request(endpoint=endpoint, method=method, params=params)

        return self.http_request(endpoint=endpoint, method=method, params=params)



    def get_klines(self, symbol: str, interval: str, start_time: int = None, end_time: int = None, timeZone: str = None, limit: int = 500):
        if self.futures:
            endpoint = '/fapi/v1/klines'
        else:
            endpoint = '/api/v3/klines'
        method = "GET"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        if start_time:
            params['start_time'] = start_time
        if timeZone:
            params['timeZone'] = timeZone

        return self.http_request(endpoint=endpoint, method=method, params=params)


    def post_limit_order(self, symbol: str, side, qnt, price, reduceOnly=False):
        if self.futures:
            endpoint = '/fapi/v1/order'
        else:
            endpoint = '/api/v3/order'
        method = "POST"
        params = {
            'symbol': symbol,
            'side': side,
            'type': "LIMIT",
            'quantity': qnt,
            'price': price,
            'timeInForce': 'GTC'
        }
        if reduceOnly:
            params['reduceOnly'] = reduceOnly


        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)


    def post_market_order(self, symbol: str, side, qnt):
        if self.futures:
            endpoint = '/fapi/v1/order'
        else:
            endpoint = '/api/v3/order'
        method = "POST"
        params = {
            'symbol': symbol,
            'side': side,
            'type': "MARKET",
            'quantity': qnt,
        }

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)





import hashlib
import hmac
import json
import time
import requests


class Bybit_api:
    BASE_LINK = "https://api.bybit.com"

    def __init__(self, api_key=None, secret_key=None, futures=False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.futures = futures
        if self.futures:
            self.category = "linear"
        else:
            self.category = "spot"
        self.header = {
            'X-BAPI-API-KEY': self.api_key,
            "X-BAPI-RECV-WINDOW": "5000",
        }

    def gen_signature(self, mod_params, timestamp):
        param_str = timestamp + self.api_key + '5000' + mod_params
        sign = hmac.new(bytes(self.secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256).hexdigest()
        return sign

    def http_request(self, method, endpoint, params):
        """
        Отправляет http запрос на сервер торговой площадки

        :param endpoint: url адрес запроса
        :param method: тип запроса (GET, POST)
        :param params: тело запроса (params)

        :return: :class:Response (requests.models.Response)
        """
        timestamp = str(int(time.time() * 1000))
        params_get_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        params_post_json = json.dumps(params)

        if method == 'GET':
            sign = self.gen_signature(params_get_string, timestamp)
            self.header['X-BAPI-SIGN'] = sign
            self.header['X-BAPI-TIMESTAMP'] = timestamp
            response = requests.get(url=self.BASE_LINK + endpoint, params=params, headers=self.header)
        elif method == "POST":
            sign = self.gen_signature(params_post_json, timestamp)
            self.header['X-BAPI-SIGN'] = sign
            self.header['X-BAPI-TIMESTAMP'] = timestamp
            response = requests.post(url=self.BASE_LINK + endpoint, data=json.dumps(params), headers=self.header)

        else:
            print("Метод не известен!")
            return None

        if response:
            response_json = response.json()
            response_headers = response.headers
            return response_json, response_headers
        else:
            return response.text, None

    def get_klines(self, symbol: str, interval: str, start: int = None, end: int = None, limit=200, headers=False):
        endpoint = "/v5/market/kline"
        method = "GET"
        params = {
            'category': self.category,
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if start:
            params['start'] = start
        if end:
            params['end'] = end

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json

    def get_server_time(self, headers=False):
        endpoint = "/v5/market/time"
        method = "GET"
        params = {}

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json

    def get_tickers(self, symbol: str = None, headers=False):
        endpoint = "/v5/market/tickers"
        method = "GET"
        params = {
            'category': self.category,
        }
        if symbol:
            params['symbol'] = symbol

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json

    def post_limit_order(self, symbol: str, side: str, qnt, price, reduce_only=False, headers=False):
        endpoint = "/v5/order/create"
        method = "POST"
        params = {
            'category': self.category,
            'symbol': symbol,
            'side': side.capitalize(),
            'orderType': 'Limit',
            'qty': str(qnt),
            'price': str(price)
        }
        if reduce_only:
            params['reduceOnly'] = reduce_only

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json

    def post_market_order(self, symbol: str, side: str, qnt, reduce_only=False, headers=False):
        endpoint = "/v5/order/create"
        method = "POST"
        params = {
            'category': self.category,
            'symbol': symbol,
            'side': side.capitalize(),
            'orderType': 'Market',
            'qty': str(qnt),
        }
        if reduce_only:
            params['reduceOnly'] = reduce_only

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json


    def post_cancel_order(self, symbol: str, orderId: str = None, orderLinkId: str = None, headers=False):
        endpoint = "/v5/order/cancel"
        method = "POST"
        params = {
            'category': self.category,
            'symbol': symbol,
        }
        if orderId:
            params['orderId'] = orderId
        elif orderLinkId:
            params['orderLinkId'] = orderLinkId
        else:
            return print("No paramether orderId")

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json


    def get_position_info(self, symbol: str = None, settleCoin: str = None, headers=False):
        endpoint = "/v5/position/list"
        method = "GET"
        params = {
            'category': self.category,
        }
        if symbol:
            params['symbol'] = symbol
        elif settleCoin:
            params['settleCoin'] = settleCoin  # USDT or USDC
        else:
            return print("No paramether settleCoin")

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json


    def get_instruments_info(self, symbol: str = None, status: str = None, baseCoin: str = None, limit: int = None, headers=False):
        endpoint = "/v5/market/instruments-info"
        method = "GET"
        params = {
            'category': self.category,
        }
        if symbol:
            params['symbol'] = symbol
        if status:
            params['status'] = status
        if baseCoin:
            params['baseCoin'] = baseCoin
        if limit:
            params['limit'] = limit

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json


    def get_fee_rate(self, symbol: str = None, baseCoin: str = None, headers=False):
        endpoint = "/v5/account/fee-rate"
        method = "GET"
        params = {
            'category': self.category,
        }
        if symbol:
            params['symbol'] = symbol
        if baseCoin:
            params['baseCoin'] = baseCoin

        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json


    def get_coins_info(self, coin: str = None, headers=False):
        endpoint = "/v5/asset/coin/query-info"
        method = "GET"
        params = {}
        if coin:
            params['coin'] = coin
        response_json, response_headers = self.http_request(method=method, endpoint=endpoint, params=params)
        if headers:
            return response_json, response_headers
        else:
            return response_json
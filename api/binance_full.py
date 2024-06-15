import hashlib
import hmac
import time
import requests


class Binance_api:
    spot_link = "https://api.binance.com"
    futures_link = "https://fapi.binance.com"
    testnet_futures_link = "https://testnet.binancefuture.com"

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

    def get_recent_trades(self, symbol: str, limit: int = 500):
        if self.futures:
            endpoint = '/fapi/v1/trades'
        else:
            endpoint = '/api/v3/trades'
        method = 'GET'
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self.http_request(endpoint=endpoint, method=method, params=params)

    def get_klines(self, symbol: str, interval: str, startTime: int = None, endTime: int = None, limit=500):
        if self.futures:
            endpoint = "/fapi/v1/klines"
        else:
            endpoint = "/api/v3/klines"
        method = "GET"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        return self.http_request(method=method, endpoint=endpoint, params=params)

    def get_order_book(self, symbol: str, limit=100):
        if self.futures:
            endpoint = "/fapi/v1/depth"
        else:
            endpoint = "/api/v3/depth"
        method = "GET"
        params = {
            'symbol': symbol,
            'limit': limit
        }

        return self.http_request(method=method, endpoint=endpoint, params=params)

    def get_server_time(self):
        if self.futures:
            endpoint = '/fapi/v1/time'
        else:
            endpoint = '/api/v3/time'

        method = "GET"

        return self.http_request(endpoint=endpoint, method=method)

    def get_mark_price(self, symbol: str = None):
        if self.futures:
            endpoint = '/fapi/v1/premiumIndex'
        else:
            return 'No Mark Price for Spot trading!'

        method = "GET"
        params = {}

        if symbol:
            params['symbol'] = symbol

        return self.http_request(endpoint=endpoint, method=method, params=params)

    def get_funding_rate_info(self):
        if self.futures:
            endpoint = '/fapi/v1/fundingInfo'
        else:
            return 'No Mark Price for Spot trading!'
        method = "GET"

        return self.http_request(endpoint=endpoint, method=method)

    def get_exchange_info(self, symbol: str = None, symbols=None):
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

    def post_limit_order(self, symbol: str, side, qnt, price, reduce_only=False):
        if self.futures:
            endpoint = "/fapi/v1/order"
        else:
            endpoint = "/api/v3/order"
        method = 'POST'
        params = {
            'symbol': symbol,
            'side': side,
            'quantity': qnt,
            'type': 'LIMIT',
            'price': price,
            'timeInForce': 'GTC'
        }
        if reduce_only:
            params['reduceOnly'] = True

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def post_market_order(self, symbol: str, side, qnt: float = None, quoteOrderQty: float = None):
        if self.futures:
            endpoint = "/fapi/v1/order"
            if not qnt:
                print("Обязательный параметр для фьючей - quantity отсутствует!")
                return
        else:
            endpoint = "/api/v3/order"
        method = 'POST'
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
        }
        if qnt or quoteOrderQty:
            if qnt:
                params['quantity'] = qnt
            if quoteOrderQty:
                params['quoteOrderQty'] = quoteOrderQty

        else:
            print("Не указан один из обизательных параметорв quantity или quoteOrderQty")
            return

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def post_futures_partial_stop_market_order(self, symbol: str, side, price, qnt):
        if self.futures:
            endpoint = "/fapi/v1/order"
            method = "POST"
            params = {
                "symbol": symbol,
                "side": side,
                "stopPrice": price,
                "quantity": qnt,
                "type": "STOP_MARKET"
            }
        else:
            print("Only for Futures market!")
            return

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def post_futures_takeprofit_market_order(self, symbol: str, side, price):
        if self.futures:
            endpoint = "/fapi/v1/order"
            method = "POST"
            params = {
                "symbol": symbol,
                "side": side,
                "stopPrice": price,
                "type": "TAKE_PROFIT_MARKET",
                "closePosition": True
            }
        else:
            print("Only for Futures market!")
            return

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def post_futures_stoploss_market_order(self, symbol: str, side, price):
        if self.futures:
            endpoint = "/fapi/v1/order"
            method = "POST"
            params = {
                "symbol": symbol,
                "side": side,
                "stopPrice": price,
                "type": "STOP_MARKET",
                "closePosition": True
            }
        else:
            print("Only for Futures market!")
            return

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def delete_cancel_order(self, symbol: str, orderId: int = None, origClientOrderId: str = None):
        if self.futures:
            endpoint = "/fapi/v1/order"
        else:
            endpoint = "/api/v3/order"
        method = 'DELETE'
        params = {
            'symbol': symbol,
        }
        if orderId or origClientOrderId:
            if orderId:
                params['orderId'] = orderId
            if origClientOrderId:
                params['origClientOrderId'] = origClientOrderId

        else:
            print("Не указан один из обизательных параметорв orderId или origClientOrderId")
            return

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def delete_cancel_all_open_orders(self, symbol: str):
        if self.futures:
            endpoint = "/fapi/v1/allOpenOrders"
        else:
            endpoint = "/api/v3/openOrders"
        method = 'DELETE'
        params = {
            'symbol': symbol,
        }

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def post_futures_trailing_stop_market_order(self, symbol, side, callbackRate, qnt, reduceOnly=True, workingType='CONTRACT_PRICE'):
        if self.futures:
            endpoint = "/fapi/v1/order"
            method = "POST"
            params = {
                "symbol": symbol,
                "side": side,
                "type": "TRAILING_STOP_MARKET",
                "callbackRate": callbackRate,  # The activation price as a percentage
                "quantity": qnt,
                "reduceOnly": reduceOnly,
                "workingType": workingType  # You can also use "MARK_PRICE"
            }
        else:
            print("Only for Futures market!")
            return

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def get_acc_info_userdata(self):
        if self.futures:
            endpoint = "/fapi/v2/account"
        else:
            endpoint = '/api/v3/account'
        method = 'GET'

        return self.http_request(endpoint=endpoint, method=method, sign_need=True)

    def get_order_info(self, symbol: str, order_id: int = None) -> list:
        if self.futures:
            endpoint = '/fapi/v1/openOrder'
        else:
            endpoint = '/api/v3/order'

        method = 'GET'
        params = {
            'symbol': symbol,
        }

        if order_id:
            params['orderId'] = order_id
        else:
            print("Не указан один из обизательных параметорв orderId или origClientOrderId")
            return []

        return self.http_request(endpoint=endpoint, method=method, params=params, sign_need=True)

    def post_listen_key(self):
        if self.futures:
            endpoint = '/fapi/v1/listenKey'
        else:
            endpoint = '/api/v3/userDataStream'
        method = "POST"

        return self.http_request(endpoint=endpoint, method=method)


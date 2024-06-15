import hashlib
import hmac
import json
import time
import requests
from api_data1.api_data import binance_testnetFutures_api_secret, binance_testnetFutures_api_keys, url_place_order
import decimal

url_wallet = "https://api.bybit.com/v5/account/wallet-balance"
data1 = {"accountType": "UNIFIED"}
recv_window = 5000
params_balance = {
    "accountType": "UNIFIED"
}
def get_timestamp():
    return str(int(time.time()*1000))

# get price ----------------------------------------
def get_price(symbol):
    url_get_price = "https://api.bybit.com/v5/market/tickers"
    params_get_price = {
        'category': 'spot',
        "symbol": symbol,
        "limit": 10
    }
    return requests.get(url=url_get_price, params=params_get_price).json()['result']['list'][0]['lastPrice']
#------------------------------------------------
# signature binance
def gen_signature_binance(params):
    param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
    signature = hmac.new(bytes(binance_testnetFutures_api_secret, "utf-8"), param_str.encode("utf-8"), hashlib.sha256).hexdigest()
    return signature

header_binance = {
    "X-MBX-APIKEY": binance_testnetFutures_api_keys
}
#-----------
# market order ---------------------------------------
def get_private_market_order_binance(symbol, side, quantity):
    params_market = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": int(time.time() * 1000),
    }
    params_market['signature'] = gen_signature_binance(params_market)
    new_market_order_binance = requests.post(url=url_place_order, params=params_market, headers=header_binance).json()  # размещение новой заявки
    return new_market_order_binance

# ------------------------------------------------------
# limit order -------------------------------------------
def get_private_limit_order_binance(symbol, side, quantity, price):
    params_limit = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": round(float(quantity),2),
        "price": int(price),
        "timestamp": int(time.time()*1000)
    }
    params_limit['signature'] = gen_signature_binance(params_limit)
    new_limit_order_binance = requests.post(url=url_place_order, params=params_limit, headers=header_binance).json()  # размещение новой заявки
    return new_limit_order_binance
#-------------------------------------------------------
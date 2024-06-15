import hashlib
import hmac
import time
import requests

url_order_futures = "https://fapi.binance.com/fapi/v1/order" #url для размещения заявки на фьючерсах
# API данные из Binance testnet
binance_api_key = "a647abe7a575ed0d13ecc55e01121379a70674d191635c96bdf7d672a0c61038"
binance_secret_key = "c66ad748ea2dbf89e02478d7d8aaf0db5da951d62f9bb85c45a114719d4e5e36"
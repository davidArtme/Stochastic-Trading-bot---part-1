import threading
import api
import datetime
import requests
import time
import hashlib
import hmac
import talib
from talib import RSI, STOCHF, WILLR
import numpy as np
from api_data1.functions1 import get_private_market_order_binance
from api_data1.api_data import binance_testnetFutures_api_keys, binance_testnetFutures_api_secret

def gen_signature(params): # генерируем сигнатуру
    param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
    signature = hmac.new(bytes(binance_testnetFutures_api_secret, "utf-8"), param_str.encode("utf-8"), hashlib.sha256).hexdigest()
    return signature

client = api.Binance_api(api_key=binance_testnetFutures_api_keys, secret_key=binance_testnetFutures_api_secret) # подставляем API данные тестнет версии бинанс
symbol = "ETHUSDT" # валютная пара
qty = 1 # количество
interval = '1m' # 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M - таймфрейм торговли на фьючерсах
limit = 60

socket_futures = f'wss://fstream.binance.com/stream?streams={symbol.lower()}@kline_{interval}' # фьючерсы
socket_spot = f'wss://stream.binance.com:9443/stream?streams={symbol.lower()}@kline_{interval}' # спот

positions = [] # список всех позиций
counter = 0 # счетчик для числа сделок

def get_klines_closed(client, symbol, interval, limit):
    '''
           Список закрытых свечей.
    '''
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)  # Получаем свечи
    klines.pop()  # Удаляем последнюю незакрытую свечу
    numpy_klines = np.array(klines)
    close_prices = numpy_klines[:, 4]  # получаем только цены закрытия из массивов
    close_prices = close_prices.astype(float)
    return close_prices
def get_klines_high(client, symbol, interval, limit):
    '''
    Список максимумов свечей.
    '''
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)  # Получаем свечи
    klines.pop()  # Удаляем последнюю незакрытую свечу
    numpy_klines = np.array(klines)
    high_prices = numpy_klines[:, 2]  # получаем только цены закрытия из массивов
    high_prices = high_prices.astype(float)
    return high_prices
def get_klines_low(client, symbol, interval, limit):
    '''
    Список минимумов свечей.
    '''
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)  # Получаем свечи
    klines.pop()  # Удаляем последнюю незакрытую свечу
    numpy_klines = np.array(klines)
    low_prices = numpy_klines[:, 3]  # получаем только цены закрытия из массивов
    low_prices = low_prices.astype(float)
    return low_prices

def stochastic_indicator_output(high_prices, low_prices, close_prices):
    '''
        Функция формирует словарь из технических индикаторов, полученных из библиотеки talib
    '''
    fastk, fastd = STOCHF(high_prices, low_prices, close_prices, fastk_period=14, fastd_period=3, fastd_matype=0) # быстрый стохастик
    current_price = get_klines_closed(client, symbol, interval, limit=limit)[-1] # текущая цена
    K = {
        'fastk': fastk, # быстрый стохастик
        'fastd': fastd, # сглаженный быстрый стохастик
        'current price': current_price # текущая цена
        }
    return K
def stochastic_strategy2(client, K):
    '''
        Функция принимает словарь из технических индикаторов.
        Если сигнал последней сделки равен 'SELL', значение предыдущего стохастика < 20 и значение текущего >= 20, то запись и открытие лонг позиции в списке позиций.
        Если сигнал последней сделки равен 'BUY', значение предыдущего стохастика > 80, и значение текущего <= 80, то запись и открытие шорт позиции в списке позиций.
        Стратегия сформирована таким образом, чтобы избегать повторного открытия позиции при возникновении ложных сигналов.
        На основе списка открытых позиций подсчитывается профит/лосс всего списка, число успешных/убыточных сделок, и сделок в ноль, а также доходность и коэффициент успеха.
    '''
    global positions, counter

    fastk_current = round(K['fastk'][-1],2) # Текущее значение стохастика
    fastk_previous = round(K['fastk'][-2],2) # Предыдущее значение стохастика
    print(f'Текущее значение стохастика в момент времени {datetime.datetime.now().time()} = {fastk_current}, предыдущее значение стохастика = {fastk_previous}')

    if fastk_previous < 20 and fastk_current >= 20: #LONG
        if not positions or positions[-1][0] == 'SELL':
            print('Вы разместили ЛОНГ ордер')
            long_order = get_private_market_order_binance('ETHUSDT', 'BUY', 0.1) # размещение приватного лонг ордера
            print(long_order)
            order_ID_Long = long_order['orderId'] # получаем ID ордера
            positions.append(['BUY', K['current price'], order_ID_Long]) # добавляем позицию в список
            counter += 1 # увеличиваем число позиций на один

    elif fastk_previous > 80 and fastk_current <= 80: #SHORT
        if not positions or positions[-1][0] == 'BUY':
            print('Вы разместили ШОРТ ордер')
            short_order = get_private_market_order_binance('ETHUSDT', 'SELL', 0.1) # размещение приватного шорт ордера
            order_ID_Short = short_order['orderId'] # получаем ID ордера
            positions.append(['SELL', K['current price'], order_ID_Short]) # добавляем позицию в список
            counter += 1 # увеличиваем число позиций на один

    print('Список позиций: ', positions)
    print('Число позиций: ', counter)

    delta_list = []
    # Цикл по списку позиций
    for i in range(len(positions) - 1):
        if positions[0][0] == "BUY" and positions[i][0] == "BUY":
            delta = positions[i + 1][1] - positions[i][1]
            delta_list.append(delta)
        elif positions[0][0] == "SELL" and positions[i][0] == "SELL":
            delta = positions[i][1] - positions[i + 1][1]
            delta_list.append(delta)
    print('Ваш общий профит/лосс', round(sum(delta_list), 2),'USDT')
    print('Число успешных сделок:', len(list(filter(lambda x: x>0, delta_list))))
    print('Число убыточных сделок:', len(list(filter(lambda x: x<0, delta_list))))
    print('Число нейтральных сделок:', len(list(filter(lambda x: x==0, delta_list))))
    print('Общее число сделок', len(delta_list))
    print(f'Ваша доходность {100 * round(sum(delta_list),2) / K['current price']} %')
    if len(delta_list) >=1:
        print(f'Коэффициент успеха: {len(list(filter(lambda x: x>0, delta_list))) / len(delta_list)}')
    print('-' * 150)

if __name__ == '__main__':
    ws_binance = api.Socket_conn_Binance_version2(socket_futures)
    threading.Thread(target=ws_binance.run_forever).start()



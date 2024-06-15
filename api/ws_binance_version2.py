# pip install websocket-client
import json
import traceback
import websocket
import threading
import time
from robot_logics3 import *


class Socket_conn_Binance_version2(websocket.WebSocketApp):
    def __init__(self, url, on_message=None, topics=None):
        super().__init__(
            url=url,
            on_open=self.on_open,
            on_message=on_message if on_message else self.on_message,  # Измененно на передачу хэндлера в майн
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.topics = topics
        self.closed_price = None
        self.closed_high_price = None
        self.closed_low_price = None
        self.historical_closes = get_klines_closed(client=client, symbol=symbol, interval=interval, limit=limit)
        self.high_prices = get_klines_high(client=client, symbol=symbol, interval=interval, limit=limit)
        self.low_prices = get_klines_low(client=client, symbol=symbol, interval=interval, limit=limit)

    def on_open(self, ws):
        print(ws, 'Websocket was opened')
        # time.sleep(15)
        if self.topics:
            self.send_subscribe(self.topics)

        # ws.close()

    def on_error(self, ws, error):
        print('on_error', ws, error)
        print(traceback.format_exc())
        exit()

    def on_close(self, ws, status, msg):
        print('on_close', ws, status, msg)
        exit()

    def on_message(self, ws,  msg):
        # при обработке этого хэндлера в майн, тут не будет выполняться дальнейшая логика... Каждый выбирает что ему удобно
        data = json.loads(msg)
        # print(data)
        if 'data' in data and data['data']['k']['x']:
            self.closed_price = float(data['data']['k']['c'])
            self.closed_high_price = float(data['data']['k']['c'])
            self.closed_low_price = float(data['data']['k']['c'])
            threading.Thread(target=self.execute).start()
            #print(self.closed_price)

    def execute(self):
        self.historical_closes = np.append(self.historical_closes, self.closed_price)
        self.historical_closes = self.historical_closes[-limit:]

        self.high_prices = np.append(self.high_prices, self.closed_high_price)
        self.high_prices = self.high_prices[-limit:]

        self.low_prices = np.append(self.low_prices, self.closed_low_price)
        self.low_prices = self.low_prices[-limit:]

        K = stochastic_indicator_output(high_prices=self.high_prices, low_prices=self.low_prices, close_prices=self.historical_closes)
        stochastic_strategy2(client=client, K=K)

    def get_closed_prices(self):
        return self.closed_price

    def send_subscribe(self, topics):
        data = {
        "method": "SUBSCRIBE",
        "params": topics,
        "id": 10054
    }
        self.send(json.dumps(data))

    # def return_data(self):
    #     return self.kline_volume

    def stop_ws(self):
        self.close()
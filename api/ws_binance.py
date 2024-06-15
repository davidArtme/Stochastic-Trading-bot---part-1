# pip install websocket-client
import json
import traceback
import websocket
import threading
import time


class Socket_conn_Binance(websocket.WebSocketApp):
    def __init__(self, url, on_message=None, topics=None):
        super().__init__(
            url=url,
            on_open=self.on_open,
            on_message=on_message if on_message else self.on_message,  # Измененно на передачу хэндлера в майн
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.topics = topics
        # self.kline_volume = None
        # self.klines_for_10_limit = None
        # self.kline = None
        self.closed_price = None


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
            print(self.closed_price)


    def get_closed_prices(self):
        return self.closed_price

    def send_subscribe(self, topics):
        data = {
        "method": "SUBSCRIBE",
        "params": topics,
        "id": 10054
    }
        self.send(json.dumps(data))

    def return_data(self):
        return self.kline_volume

    def stop_ws(self):
        self.close()
import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

import orders

class SubAction:
    def __init__(self, config):
        self.leverage = config["leverage"]
        self.volatility_term = config["volatility_term"]
        self.stop_range = config["stop_range"]
        self.trade_risk = config["trade_risk"]
        self.entry_times = config["entry_times"]
        self.entry_range = config["entry_range"]

        self.bitflyer = orders.Order()


    # CryptowatchのAPIを使用する関数
    def get_price(self, min, before=0, after=0):
        price = []
        params = {"periods" : min }
        if before != 0:
            params["before"] = before
        if after != 0:
            params["after"] = after

        response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params)
        data = response.json()

        if data["result"][str(min)] is not None:
            for i in data["result"][str(min)]:
                if i[1] != 0 and i[2] != 0 and i[3] != 0 and i[4] != 0:
                    price.append({ "close_time" : i[0],
                        "close_time_dt" : datetime.fromtimestamp(i[0]).strftime('%Y/%m/%d %H:%M'),
                        "open_price" : i[1],
                        "high_price" : i[2],
                        "low_price" : i[3],
                        "close_price": i[4] })
            return price

        else:
            print("データが存在しません")
            return None

    # json形式のファイルから価格データを読み込む関数
    def get_price_from_file(self, path):
        file = open(path,'r',encoding='utf-8')
        price = json.load(file)
        return price

    # 時間と始値・終値を表示する関数
    def print_price(self, data):
        print( "時間： " + datetime.fromtimestamp(data["close_time"]).strftime('%Y/%m/%d %H:%M') + " 高値： " + str(data["high_price"]) + " 安値： " + str(data["low_price"]) )

    def log_price(self, data, flag):
        log = "時間： " + datetime.fromtimestamp(data["close_time"]).strftime('%Y/%m/%d %H:%M') + " 始値： " + str(data["open_price"]) + " 終値： " + str(data["close_price"]) + "\n"
        flag["records"]["log"].append(log)
        return flag


    def calculate_volatility(self, last_data):

        high_sum = sum(i["high_price"] for i in last_data[-1 * self.volatility_term: ])
        low_sum = sum(i["low_price"] for i in last_data[-1 * self.volatility_term: ])
        volatility = round((high_sum - low_sum) / self.volatility_term)
        return volatility


    def calculate_lot(self, last_data, data, flag):

        lot = 0
        #口座残高を取得する（バックテスト用）
        balance = flag["records"]["funds"]

        #口座残高を取得する（フォワードテスト用）
        # balance = self.bitflyer.get_bitflyer_collateral()

        #最初のエントリーの場合
        if flag["add-position"]["count"] == 0:

            # 1回の注文単位と基準レンジを計算する
            volatility = self.calculate_volatility(last_data)
            stop = self.stop_range * volatility
            calc_lot = np.floor(balance * self.trade_risk / stop * 100) / 100

            flag["add-position"]["unit-size"] = np.floor(calc_lot / self.entry_times * 100) / 100
            flag["add-position"]["unit-range"] = round(volatility * self.entry_range)
            flag["add-position"]["stop"] = stop
            flag["position"]["ATR"] = round(volatility)

            flag["records"]["log"].append("\n現在のアカウント残高は{}円です\n".format(balance))
            flag["records"]["log"].append("許容リスクから購入できる枚数は最大{}BTCまでです\n".format(calc_lot))
            flag["records"]["log"].append("{0}回に分けて{1}BTCずつ注文します\n".format(self.entry_times, flag["add-position"]["unit-size"]))

        #2回目以降のエントリーの場合
        else:
            balance = round(balance - flag["position"]["price"] * flag["position"]["lot"] / self.leverage)

        #ストップ幅には、最初のエントリー時に計算したボラティリティを使う
        stop = flag["add-position"]["stop"]

        #注文可能なロット数を計算する
        able_lot = np.floor(balance * self.leverage / data["close_price"] * 100) / 100
        lot = min(able_lot, flag["add-position"]["unit-size"])

        flag["records"]["log"].append("証拠金から購入できる枚数は最大{}BTCまでです\n".format(able_lot))

        return lot, stop, flag

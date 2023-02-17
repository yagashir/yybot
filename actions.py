import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

import strategies
import sub_actions
import backtest_output

class Actions:
    def __init__(self):
        self.strategy = strategies.Strategies()
        self.sub_action = sub_actions.SubActions()
        self.backtest = backtest_output.Backtest()
        self.need_term = 0
        self.chart_sec = 3600
        pass

    def entry_signal(self, data, last_data, flag):
        signal = self.strategy.donchian(data, last_data)

        if signal["side"] == "BUY":
            flag["records"]["log"].append("過去{0}足の最高値{1}円を、直近の高値が{2}円でブレイクしました\n".format(self.need_term,signal["price"],data["high_price"]))
            flag["records"]["log"].append(str(data["close_price"]) + "円で買いの指値注文を出します\n")

            lot, stop = self.sub_action.calculate_lot(last_data, data, flag)
            if lot > 0.01:
                print("{0}円あたりに{1}BTCで買いの注文を出します\n".format(data["close_price"], lot))

                #買い注文のコードを入れる

                flag["records"]["log"].append("{0}円にストップを入れます\n".format(data["close_price"] - stop))
                flag["order"]["lot"], flag["order"]["stop"] = lot, stop
                flag["order"]["exist"] = True
                flag["order"]["side"] = "BUY"
                flag["order"]["price"] = data["close_price"]
            else:
                print("注文可能枚数{}が、最低注文単位に満たなかったので注文を見送ります".format(lot))

        if signal["side"] == "SELL":
            flag["records"]["log"].append("過去{0}足の最安値{1}円を、直近の安値が{2}円でブレイクしました\n".format(self.need_term,signal["price"],data["low_price"]))
            flag["records"]["log"].append(str(data["close_price"]) + "円で売りの指値注文を出します\n")

            lot, stop = self.sub_action.calculate_lot(last_data, data, flag)
            if lot > 0.01:
                print("{0}円あたりに{1}BTCで売りの注文を出します\n".format(data["close_price"], lot))

                #売り注文のコードを入れる

                flag["records"]["log"].append("{0}円にストップを入れます\n".format(data["close_price"] + stop))
                flag["order"]["lot"], flag["order"]["stop"] = lot, stop
                flag["order"]["exist"] = True
                flag["order"]["side"] = "SELL"
                flag["order"]["price"] = data["close_price"]
            else:
                print("注文可能枚数{}が、最低注文単位に満たなかったので注文を見送ります".format(lot))

        return flag


    # サーバーに出した注文が約定したか確認する関数
    def check_order(self, flag):

        # 注文状況を確認して通っていたら以下を実行
        # 一定時間で注文が通っていなければキャンセルする

        flag["order"]["exist"] = False
        flag["order"]["count"] = 0
        flag["position"]["exist"] = True
        flag["position"]["side"] = flag["order"]["side"]
        flag["position"]["stop"] = flag["order"]["stop"]
        flag["position"]["price"] = flag["order"]["price"]
        flag["position"]["lot"] = flag["order"]["lot"]

        return flag


    def close_position(self, data, last_data, flag):

        #既に損切にかかっていたら何もしない
        if flag["position"]["exist"] == False:
            return flag

        flag["position"]["count"] += 1
        signal = self.strategy.donchian(data, last_data)

        if flag["position"]["side"] == "BUY":
            if signal["side"] == "SELL":
                log = "過去"+ str(self.need_term) + "足の最安値"+ str(signal["price"]) + "円を、直近の安値が"+ str(data["low_price"]) + "円でブレイクした\n"
                log += "成行注文を出してポジションを決済します\n"
                flag["records"]["log"].append(log)

                #決済の成行注文コードを入れる

                self.backtest.records(flag, data, data["close_price"])
                flag["position"]["exist"] = False
                flag["position"]["count"] = 0

                lot, stop = self.sub_action.calculate_lot(last_data, data, flag)
                if lot > 0.01:

                    log = "さらに" + str(data["close_price"]) + "円で売りの指値注文を入れてドテンします\n"
                    flag["records"]["log"].append(log)

                    #売り注文のコードを入れる

                    flag["records"]["log"].append("{0}円にストップを入れます\n".format(data["close_price"] + stop))
                    flag["order"]["lot"],flag["order"]["stop"] = lot,stop
                    flag["order"]["exist"] = True
                    flag["order"]["side"] = "SELL"
                    flag["order"]["price"] = data["close_price"]


        if flag["position"]["side"] == "SELL":
            if signal["side"] == "BUY":
                log = "過去"+ str(self.need_term) + "足の最高値"+ str(signal["price"]) + "円を、直近の高値が"+ str(data["high_price"]) + "円でブレイクした\n"
                log += "成行注文を出してポジションを決済します\n"
                flag["records"]["log"].append(log)

                #決済の成行注文コードを入れる

                self.backtest.records(flag, data, data["close_price"])
                flag["position"]["exist"] = False
                flag["position"]["count"] = 0

                lot, stop = self.sub_action.calculate_lot(last_data, data, flag)
                if lot > 0.01:

                    log = "さらに" + str(data["close_price"]) + "で買いの指値注文を入れてドテンします\n"
                    flag["records"]["log"].append(log)

                    #買いの注文コードを入れる

                    flag["records"]["log"].append("{0}円にストップを入れます\n".format(data["close_price"] - stop))
                    flag["order"]["lot"],flag["order"]["stop"] = lot,stop
                    flag["order"]["exist"] = True
                    flag["order"]["side"] = "BUY"
                    flag["order"]["price"] = data["close_price"]

        return flag


    #損切関数
    def stop_position(self, data, last_data, flag):

        if flag["position"]["side"] == "BUY":
            stop_price = flag["position"]["price"] - flag["position"]["stop"]
            if data["low_price"] < stop_price:
                flag["records"]["log"].append("{0}円の損切ラインに引っかかりました。\n".format(stop_price))
                stop_price = round(stop_price - 2 * self.sub_action.calculate_volatility(last_data) / (self.chart_sec / 60))
                flag["records"]["log"].append(str(stop_price) + "円あたりで成行注文を出してポジションを決済します\n")

                #決済の成行注文コードを入れる

                self.backtest.records(flag, data, stop_price, "STOP")
                flag["position"]["exist"] = False
                flag["position"]["count"] = 0

        if flag["position"]["side"] == "SELL":
            stop_price = flag["position"]["price"] + flag["position"]["stop"]
            if data["high_price"] > stop_price:
                flag["records"]["log"].append("{0}円の損切ラインに引っかかりました。\n".format(stop_price))
                stop_price = round(stop_price + 2 * self.sub_action.calculate_volatility(last_data) / (self.chart_sec / 60))
                flag["records"]["log"].append(str(stop_price) + "円あたりで成行注文を出してポジションを決済します\n")

                #決済の成行注文コードを入れる

                self.backtest.records(flag, data, stop_price, "STOP")
                flag["position"]["exist"] = False
                flag["position"]["count"] = 0

        return flag
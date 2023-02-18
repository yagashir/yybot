import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

import strategies
import orders
import sub_actions
import backtest_output

class Action:
    def __init__(self, config):
        self.need_term = config["need_term"]
        self.chart_sec = config["chart_sec"]
        self.slippage = config["slippage"]
        self.entry_times = config["entry_times"]
        self.entry_range = config["entry_range"]

        self.strategy = strategies.Strategy(config)
        self.sub_action = sub_actions.SubAction(config)
        self.backtest = backtest_output.Backtest(config)
        self.order = orders.Order()


        pass

    def entry_signal(self, data, last_data, flag):
        signal = self.strategy.donchian(data, last_data)

        if signal["side"] == "BUY":
            flag["records"]["log"].append("過去{0}足の最高値{1}円を、直近の高値が{2}円でブレイクしました\n".format(self.need_term,signal["price"],data["high_price"]))
            flag["records"]["log"].append(str(data["close_price"]) + "円で買いの指値注文を出します\n")

            lot, stop, flag = self.sub_action.calculate_lot(last_data, data, flag)
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

            lot, stop, flag = self.sub_action.calculate_lot(last_data, data, flag)
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
                flag["add-position"]["count"] = 0

                lot, stop, flag = self.sub_action.calculate_lot(last_data, data, flag)
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
                flag["add-position"]["count"] = 0

                lot, stop, flag = self.sub_action.calculate_lot(last_data, data, flag)
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
                flag["records"]["log"].append("{0} 円の損切ラインに引っかかりました。\n".format(stop_price))
                stop_price = round(stop_price - 2 * self.sub_action.calculate_volatility(last_data) / (self.chart_sec / 60))
                flag["records"]["log"].append(str(stop_price) + "円あたりで成行注文を出してポジションを決済します\n")

                #決済の成行注文コードを入れる

                self.backtest.records(flag, data, stop_price, "STOP")
                flag["position"]["exist"] = False
                flag["position"]["count"] = 0
                flag["add-position"]["count"] = 0

        if flag["position"]["side"] == "SELL":
            stop_price = flag["position"]["price"] + flag["position"]["stop"]
            if data["high_price"] > stop_price:
                flag["records"]["log"].append("{0} 円の損切ラインに引っかかりました。\n".format(stop_price))
                stop_price = round(stop_price + 2 * self.sub_action.calculate_volatility(last_data) / (self.chart_sec / 60))
                flag["records"]["log"].append(str(stop_price) + "円あたりで成行注文を出してポジションを決済します\n")

                #決済の成行注文コードを入れる

                self.backtest.records(flag, data, stop_price, "STOP")
                flag["position"]["exist"] = False
                flag["position"]["count"] = 0
                flag["add-position"]["count"] = 0

        return flag

    #複数回に分けて追加ポジションを取る関数
    def add_position(self, data, last_data, flag):

        #ポジションがない場合は何もしない
        if flag["position"]["exist"] == False:
            return flag

        #最初（1回目）のエントリー価格を記録
        if flag["add-position"]["count"] == 0:
            flag["add-position"]["first-entry-price"] = flag["position"]["price"]
            flag["add-position"]["last-entry-price"] = flag["position"]["price"]
            flag["add-position"]["count"] += 1

        while True:

            #以下の場合は、追加ポジションを取らない
            if flag["add-position"]["count"] >= self.entry_times:
                return flag

            #関数内で使う変数を用意
            first_entry_price = flag["add-position"]["first-entry-price"]
            last_entry_price = flag["add-position"]["last-entry-price"]
            unit_range = flag["add-position"]["unit-range"]
            current_price = data["close_price"]

            #価格がエントリー方向に基準レンジ分だけ進んだか判定する
            should_add_position = False
            if flag["position"]["side"] == "BUY" and (current_price - last_entry_price) > unit_range:
                should_add_position = True
            elif flag["position"]["side"] == "SELL" and (last_entry_price - current_price) > unit_range:
                should_add_position = True
            else:
                break

            #基準レンジ分進んでいれば追加注文を出す
            if should_add_position:
                flag["records"]["log"].append("\n前回のエントリー価格{0}円からブレイクアウトの方向に {1} ATR ({2} 円) 以上動きました\n".format(last_entry_price, self.entry_range, round(unit_range)))
                flag["records"]["log"].append("{0}/{1} 回目の追加注文を出します\n".format(flag["add-position"]["count"] + 1, self.entry_times))

                #注文サイズを計算
                lot, stop, flag = self.sub_action.calculate_lot(last_data, data, flag)
                if lot < 0.01:
                    flag["records"]["log"].append("注文可能枚数 {} が、最低注文単位に満たなかったので注文を見送ります\n".format(lot))
                    flag["add-position"]["count"] += 1
                    return flag

                #追加注文を出す
                if flag["position"]["side"] == "BUY":
                    entry_price = first_entry_price + (flag["add-position"]["count"] * unit_range) #バックテスト用
                    entry_price = round(1 + self.slippage) * entry_price

                    flag["records"]["log"].append("現在のポジションに追加して、{0} 円で {1} BTC の買い注文を出します\n".format(entry_price, lot))

                    # ここに買い注文を入れる

                if flag["position"]["side"] == "SELL":
                    entry_price = first_entry_price - (flag["add-position"]["count"] * unit_range) #バックテスト用
                    entry_price = round(1 - self.slippage) * entry_price

                    flag["records"]["log"].append("現在のポジションに追加して、{0} 円で {1} BTC の買い注文を出します\n".format(entry_price, lot))

                    # ここに売り注文を入れる

                #ポジション全体の情報を更新する
                flag["position"]["stop"] = stop
                flag["position"]["price"] = int(round((flag["position"]["price"] * flag["position"]["lot"] + entry_price * lot) / (flag["position"]["lot"] + lot)))
                flag["position"]["lot"] = np.round((flag["position"]["lot"] + lot) * 100) / 100

                if flag["position"]["side"] == "BUY":
                    flag["records"]["log"].append("{0} 円の位置にストップを更新します\n".format(flag["position"]["price"] - stop))
                elif flag["position"]["side"] == "SELL":
                    flag["records"]["log"].append("{0} 円の位置にストップを更新します\n".format(flag["position"]["price"] + stop))

                flag["records"]["log"].append("現在のポジションの取得単価は {} 円です\n".format(flag["position"]["price"]))
                flag["records"]["log"].append("現在のポジションサイズは {} BTC です\n".format(flag["position"]["lot"]))

                flag["add-position"]["count"] += 1
                flag["add-position"]["last-entry-price"] = entry_price

        return flag


import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

import actions
import sub_actions
import strategies
import backtest_output
import orders

#--------設定項目--------

# 設定ファイルの読み込み
config = open("config.json", "r", encoding="utf-8")
config = json.load(config)
config["need_term"] = max(config["buy_term"], config["sell_term"], config["volatility_term"])


action = actions.Action()
sub_action = sub_actions.SubAction()
strategy = strategies.Strategy()
backtest = backtest_output.Backtest()


action.need_term = config["need_term"]
action.chart_sec = config["chart_sec"]
sub_action.leverage = config["leverage"]
sub_action.volatility_term = config["volatility_term"]
sub_action.stop_range = config["stop_range"]
sub_action.trade_risk = config["trade_risk"]
strategy.buy_term = config["buy_term"]
strategy.sell_term = config["sell_term"]
strategy.judge_price = config["judge_price"]
backtest.slippage = config["slippage"]
backtest.start_funds = config["start_funds"]


#価格チャートを取得
price = sub_action.get_price(config["chart_sec"])
# price = sub_action.get_price_from_file("../latest_data/1514764800-1670371200-price_1d.json")

flag = open("bt_variance.json", "r", encoding="utf-8")
flag = json.load(flag)
flag["funds"] = config["start_funds"]


last_data = []
i = 0
while i < len(price):

    if len(last_data) < config["need_term"]:
        last_data.append(price[i])
        flag = sub_action.log_price(price[i], flag)
        time.sleep(config["wait"])
        i += 1
        continue

    data = price[i]
    flag = sub_action.log_price(data, flag)

    if flag["order"]["exist"]:
        flag = action.check_order(flag)
    elif flag["position"]["exist"]:
        flag = action.stop_position(data, last_data, flag)
        flag = action.close_position(data, last_data, flag)
    else:
        flag = action.entry_signal(data, last_data, flag)

    last_data.append(data)
    i += 1
    time.sleep(config["wait"])

print("--------------------------")
print("テスト期間：")
print("開始時点：" + str(price[0]["close_time_dt"]))
print("終了時点：" + str(price[-1]["close_time_dt"]))
print(str(len(price)) + "件のローソク足データで検証")
print("--------------------------")

backtest.backtesting(flag)

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
import indicator
import backtest_output
import orders

#--------設定項目--------

#設定ファイルの読み込み
config = open("config.json", "r", encoding="utf-8")
config = json.load(config)

#設定ファイルの更新
config["need_term"] = max(config["buy_term"], config["sell_term"], config["volatility_term"])

#トレイリングストップの比率に 0~1 のスコープ外の数値を設定できないようにする
if config["trail_ratio"] > 1:
    config["trail_ratio"] = 1
elif config["trail_ratio"] < 0:
    config["trail_ratio"] = 0

#インスタンス生成
action = actions.Action(config)
sub_action = sub_actions.SubAction(config)
strategy = strategies.Strategy(config)
indicator = indicator.Indicator()
backtest = backtest_output.Backtest(config)


#価格チャートを取得
# price = sub_action.get_price(config["chart_sec"])
price = sub_action.get_price_from_file(config["chart_path"])


#バックテスト用の変数を用意
flag = open("backtest_variance.json", "r", encoding="utf-8")
flag = json.load(flag)

#バックテスト用変数の更新
flag["funds"] = config["start_funds"]
flag["stop-AF"] = config["stop_AF"]


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
        flag = action.add_position(data, last_data, flag)

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

backtest.backtesting(last_data, flag)

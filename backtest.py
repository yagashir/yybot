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


#--------設定項目--------

chart_sec = 3600
buy_term = 30
sell_term = 30


judge_price = {
    "BUY": "high_price",
    "SELL": "low_price"
}

volatility_term = 30
stop_range = 2       #何レンジ幅にストップを入れるか
trade_risk = 0.02    #1トレードあたり口座の何％まで損失を許容するか
leverage = 3         #レバレッジ倍率の設定
start_funds = 300000

need_term = max(buy_term, sell_term, volatility_term)
wait = 0
slippage = 0.001


action = actions.Actions()
sub_action = sub_actions.SubActions()
strategy = strategies.Strategies()
backtest = backtest_output.Backtest()


action.need_term = need_term
action.chart_sec = chart_sec
sub_action.leverage = leverage
sub_action.volatility_term = volatility_term
sub_action.stop_range = stop_range
sub_action.trade_risk = trade_risk
strategy.buy_term = buy_term
strategy.sell_term = sell_term
strategy.judge_price = judge_price
backtest.slippage = slippage
backtest.start_funds = start_funds


#価格チャートを取得
price = sub_action.get_price(chart_sec)
# price = sub_action.get_price_from_file("../latest_data/1514764800-1670371200-price_1d.json")


flag = {
    "order": {
        "exist": False,
        "side": "",
        "price": 0,
        "stop": 0,
        "ATR": 0,
        "lot": 0,
        "count": 0
    },
    "position": {
        "exist": False,
        "side": "",
        "price": 0,
        "stop": 0,
        "ATR": 0,
        "lot": 0,
        "count": 0
    },
    "records": {
        "date": [],
        "profit": [],
        "return": [],
        "side": [],
        "stop-count": [],
        "holding-periods": [],
        "drawdown": 0,
        "slippage": [],
        "log": [],
        "funds": start_funds
    }
}

last_data = []
i = 0
while i < len(price):

    if len(last_data) < need_term:
        last_data.append(price[i])
        flag = sub_action.log_price(price[i], flag)
        time.sleep(wait)
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
    time.sleep(wait)

print("--------------------------")
print("テスト期間：")
print("開始時点：" + str(price[0]["close_time_dt"]))
print("終了時点：" + str(price[-1]["close_time_dt"]))
print(str(len(price)) + "件のローソク足データで検証")
print("--------------------------")

backtest.backtesting(flag)

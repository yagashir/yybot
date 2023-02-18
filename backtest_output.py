import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

class Backtest:
    def __init__(self, config):
        self.slippage = config["slippage"]
        self.start_funds = config["start_funds"]
        self.output_path = config["output_path"]


    #各トレードのパフォーマンスを記録する関数
    def records(self, flag, data, close_price, close_type=None):

        #取引手数料の計算
        entry_price = int(round(flag["position"]["price"] * flag["position"]["lot"]))
        exit_price = int(round(close_price * flag["position"]["lot"]))
        trade_cost = round(exit_price * self.slippage)

        log = "スリッページ・手数料として" + str(trade_cost) + "円を考慮します\n"
        flag["records"]["log"].append(log)
        flag["records"]["slippage"].append(trade_cost)

        #手仕舞った日時と保有期間の記録
        flag["records"]["date"].append(data["close_time_dt"])
        flag["records"]["holding-periods"].append(flag["position"]["count"])

        #損切にかかった回数をカウント
        if close_type == "STOP":
            flag["records"]["stop-count"].append(1)
        else:
            flag["records"]["stop-count"].append(0)

        #値幅の計算
        buy_profit = exit_price - entry_price - trade_cost
        sell_profit = entry_price - exit_price - trade_cost

        #利益が出ているかの計算
        if flag["position"]["side"] == "BUY":
            flag["records"]["side"].append("BUY")
            flag["records"]["profit"].append(buy_profit)
            flag["records"]["return"].append(round(buy_profit / entry_price * 100, 4))
            flag["records"]["funds"] += buy_profit

            if buy_profit > 0:
                log = str(buy_profit) + "円の利益です\n"
                flag["records"]["log"].append(log)
            else:
                log = str(buy_profit) + "円の損失です\n"
                flag["records"]["log"].append(log)

        if flag["position"]["side"] == "SELL":
            flag["records"]["side"].append("SELL")
            flag["records"]["profit"].append(sell_profit)
            flag["records"]["return"].append(round(sell_profit / entry_price * 100, 4))
            flag["records"]["funds"] += sell_profit

            if sell_profit > 0:
                log = str(sell_profit) + "円の利益です\n"
                flag["records"]["log"].append(log)
            else:
                log = str(sell_profit) + "円の損失です\n"
                flag["records"]["log"].append(log)

        return flag


    #バックテストの集計用の関数
    def backtesting(self, flag):

        #成績を記録した pandas DataFrame を作成
        records = pd.DataFrame({
            "Date": pd.to_datetime(flag["records"]["date"]),
            "Profit": flag["records"]["profit"],
            "Side": flag["records"]["side"],
            "Rate": flag["records"]["return"],
            "STOP": flag["records"]["stop-count"],
            "Periods": flag["records"]["holding-periods"],
            "Slippage": flag["records"]["slippage"]
        })

        #連敗回数をカウントする
        consecutive_defeats = []
        defeats = 0
        for p in flag["records"]["profit"]:
            if p < 0:
                defeats += 1
            else:
                #連敗の記録
                consecutive_defeats.append(defeats)
                defeats = 0

        #総損益の列を追加する
        records["Gross"] = records["Profit"].cumsum()

        #資産推移の列を追加
        records["Funds"] = records["Gross"] + self.start_funds

        #最大ドローダウンの列を追加する
        records["Drawdown"] = records["Funds"].cummax().subtract(records["Funds"])
        records["DrawdownRate"] = round(records["Drawdown"] / records["Funds"].cummax() * 100, 1)

        #買いエントリと売りエントリだけをそれぞれ抽出する
        buy_records = records[records["Side"].isin(["BUY"])]
        sell_records = records[records["Side"].isin(["SELL"])]

        #月別のデータを集計する
        records["月別集計"] = pd.to_datetime(records["Date"].apply(lambda x: x.strftime("%Y/%m")))
        grouped = records.groupby("月別集計")

        #月別の成績
        month_records = pd.DataFrame({
            "Number": grouped["Profit"].count(),
            "Gross": grouped["Gross"].sum(),
            "Funds": grouped["Funds"].last(),
            "Rate": round(grouped["Rate"].mean(), 2),
            "Drawdown": grouped["Drawdown"].max(),
            "Periods": grouped["Periods"].mean()
        })

        print("バックテストの結果")
        print("--------------------------")
        print("買いエントリの成績")
        print("--------------------------")
        print("トレード回数　： {}回".format(len(buy_records)))
        print("勝率　　　　　： {}％".format(round(len(buy_records[buy_records["Profit"] > 0]) / len(buy_records) * 100, 1)))
        print("平均リターン　： {}％".format(round(buy_records["Rate"].mean(), 2)))
        print("総利益　　　　： {}円".format(buy_records["Profit"].sum()))
        print("平均保有期間　： {}足分".format(round(buy_records["Periods"]).mean(), 1))
        print("損切の回数　　： {}回".format(buy_records["STOP"].sum()))

        print("--------------------------")
        print("売りエントリの成績")
        print("--------------------------")
        print("トレード回数　： {}回".format(len(sell_records)))
        print("勝率　　　　　： {}％".format(round(len(sell_records[sell_records["Profit"] > 0]) / len(sell_records) * 100, 1)))
        print("平均リターン　： {}％".format(round(sell_records["Rate"].mean(), 2)))
        print("総利益　　　　： {}円".format(sell_records["Profit"].sum()))
        print("平均保有期間　： {}足分".format(round(sell_records["Periods"]).mean(), 1))
        print("損切の回数　　： {}回".format(round(sell_records["STOP"].sum())))

        print("--------------------------")
        print("総合の成績")
        print("--------------------------")
        print("全トレード数　　　： {}回".format(len(records)))
        print("勝率　　　　　　　： {}％".format(round(len(records[records["Profit"] > 0]) / len(records) * 100, 1)))
        print("平均リターン　　　： {}％".format(round(records["Rate"].mean(), 2)))
        print("平均保有期間　　　： {}足分".format(round(records["Periods"].mean(), 1)))
        print("損切の回数　　　　： {}回".format(records["STOP"].sum()))
        print("")
        print("最大の勝ちトレード： {}円".format(records["Profit"].max()))
        print("最大の負けトレード： {}円".format(records["Profit"].min()))
        print("最大連敗回数　　　： {}回".format(max(consecutive_defeats)))
        print("最大ドローダウン　： {0}円 / {1}%".format(-1 * records["Drawdown"].max(), -1 * records["DrawdownRate"].loc[records["Drawdown"].idxmax()]))
        print("利益合計　　　　　： {}円".format(records[records["Profit"] > 0]["Profit"].sum()))
        print("損益合計　　　　　： {}円".format(records[records["Profit"] < 0]["Profit"].sum()))
        print("最終損益　　　　　： {}円".format(records["Profit"].sum()))
        print("")
        print("初期資金　　　　　： {}円".format(self.start_funds))
        print("最終資金　　　　　： {}円".format(records["Funds"].iloc[-1]))
        print("運用成績　　　　　： {}％".format(round(records["Funds"].iloc[-1] / self.start_funds * 100, 2)))
        print("手数料合計　　　　： {}円".format(-1 * records["Slippage"].sum()))

        print("------------------------------")
        print("月別の成績")

        for index, row in month_records.iterrows():
            print("--------------------------")
            print("{0}年{1}月の成績".format(index.year, index.month))
            print("--------------------------")
            print("トレード数　　　： {}回".format(row["Number"].astype(int)))
            print("月間損益　　　　： {}円".format(row["Gross"].astype(int)))
            print("平均リターン　　： {}％".format(row["Rate"]))
            print("月間ドローダウン： {}円".format(-1 * row["Drawdown"].astype(int)))
            print("月末資金　　　　： {}円".format(row["Funds"].astype(int)))

        file = open(self.output_path + "{0}-donchian-log.txt".format(datetime.now().strftime("%Y-%m-%d-%H-%M")), "wt", encoding="utf-8")
        file.writelines(flag["records"]["log"])


        #損益曲線をプロット
        plt.plot(records["Date"], records["Funds"])
        plt.xlabel("Date")
        plt.ylabel("Balance")
        plt.xticks(rotation=50) # X軸の目盛りを 50 度回転

        plt.show()

        return

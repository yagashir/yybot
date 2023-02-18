class Strategy:
    def __init__(self):
        self.buy_term = 30
        self.sell_term = 30
        self.judge_price = {
            "BUY": "high_price",
            "SELL": "low_price"
            }


    def donchian(self, data, last_data):

        highest = max(i["high_price"] for i in last_data[(-1 * self.buy_term): ])
        if data[self.judge_price["BUY"]] > highest:
            return {"side": "BUY", "price": highest}

        lowest = min(i["low_price"] for i in last_data[(-1 * self.sell_term): ])
        if data[self.judge_price["SELL"]] < lowest:
            return {"side": "SELL", "price": lowest}

        return {"side": None, "price": 0}
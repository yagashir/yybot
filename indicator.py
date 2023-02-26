class Indicator:
    def __init__(self):
        pass

    def MA(self, last_data, timeperiod, before=None):
        if before is not None:
            ma = sum(i["close_price"] for i in last_data[(-1 * timeperiod + before): before]) / timeperiod
        else:
            ma = sum(i["close_price"] for i in last_data[-1 * timeperiod:]) / timeperiod
        return round(ma)
    

    def EMA(self, last_data, timeperiod, before=None):
        if before is not None:
            ma = sum(i["close_price"] for i in last_data[-2 * timeperiod + before: -1 * timeperiod + before]) / timeperiod
            ema = (last_data[-1 * timeperiod + before]["close_price"] * 2 / (timeperiod + 1)) + (ma * (timeperiod - 1) / (timeperiod + 1))
            for i in range(timeperiod - 1):
                ema = (last_data[-1 * timeperiod + 1 + i + before]["close_price"] * 2 / (timeperiod + 1)) + (ema * (timeperiod - 1) / (timeperiod + 1))

        else:
            ma = sum(i["close_price"] for i in last_data[-2 * timeperiod: -1 * timeperiod]) / timeperiod
            ema = (last_data[-1 * timeperiod]["close_price"] * 2 / (timeperiod + 1)) + (ma * (timeperiod - 1) / (timeperiod + 1))
            for i in range(timeperiod - 1):
                ema = (last_data[-1 * timeperiod + 1 + i]["close_price"] * 2 / (timeperiod + 1)) + (ema * (timeperiod - 1) / (timeperiod + 1))

        return round(ema)
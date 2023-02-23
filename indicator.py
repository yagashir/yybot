class Indicator:
    def __init__(self):
        pass

    def MA(self, last_data, timeperiod):
        ma = sum(i["close_price"] for i in last_data[-1 * timeperiod:]) / timeperiod
        return ma
    
import ccxt
import time

class Order:
    def __init__(self):
        self.bitflyer = ccxt.bitflyer()
        pass

    def get_bitflyer_collateral():
        while True:
            try:
                collateral = self.bitflyer.private_get_getcollateral()
                print("現在のアカウント残高は{}円です".format(int(collateral["collateral"])))
                return int(collateral["collateral"])

            except ccxt.BaseError as e:
                print("BitflyerのAPIでの口座残高取得に失敗しました")
                print("20秒待機してやり直します")
                time.sleep(20)


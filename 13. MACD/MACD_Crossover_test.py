import pandas as pd
import backtrader as bt
import os
import time

class MACDCrossoverStrategy(bt.Strategy):
    params = (
        ('fast_length', 8),
        ('slow_length', 16),
        ('signal_length', 11),
    )

    def __init__(self):
        fast_ema = bt.ind.EMA(self.data.close, period=self.p.fast_length)
        slow_ema = bt.ind.EMA(self.data.close, period=self.p.slow_length)
        self.macd = fast_ema - slow_ema
        self.signal = bt.ind.SMA(self.macd, period=self.p.signal_length)

    def next(self):
        prev_macd = self.macd[-1]
        curr_macd = self.macd[0]
        prev_signal = self.signal[-1]
        curr_signal = self.signal[0]
        if prev_macd < prev_signal and curr_macd > curr_signal and not self.position:
            self.buy()
        elif prev_macd > prev_signal and curr_macd < curr_signal and self.position:
            self.close()

# 데이터 불러오기
file_path = "./BTC_1d.csv"
btc_data = pd.read_csv(file_path)
btc_data = btc_data.rename(columns={
    'Open_time': 'datetime',
    '시가': 'open',
    '고가': 'high', 
    '저가': 'low',
    '종가': 'close',
    '거래량': 'volume'
})
btc_data = btc_data[['datetime', 'open', 'high', 'low', 'close', 'volume']]
btc_data['datetime'] = pd.to_datetime(btc_data['datetime'])
btc_data.set_index('datetime', inplace=True)

class CustomData(bt.feeds.PandasData):
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )

data_feed = CustomData(dataname=btc_data)

cerebro = bt.Cerebro(optreturn=False)
cerebro.broker.setcommission(commission=0.05 / 100, leverage=100)
cerebro.broker.setcash(10000)
cerebro.broker.set_coc(True)
cerebro.adddata(data_feed)

cerebro.optstrategy(
    MACDCrossoverStrategy,
    fast_length=range(6, 15, 2),
    slow_length=range(14, 25, 2),
    signal_length=range(9, 13)
)

results = cerebro.run(maxcpus=1)

final_results_list = []
for strat_list in results:
    strat = strat_list[0]
    value = strat.broker.getvalue()
    params = strat.params
    final_results_list.append({
        'fast': params.fast_length,
        'slow': params.slow_length,
        'signal': params.signal_length,
        'final_value': value
    })

results_df = pd.DataFrame(final_results_list)
results_df = results_df.sort_values(by='final_value', ascending=False)
print(results_df.head(10))  # 상위 10개 조합 출력

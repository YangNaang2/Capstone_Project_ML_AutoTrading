import pandas as pd
import backtrader as bt
import time
import os
import quantstats as qs

# CSV 파일 경로 및 데이터 불러오기
file_path = "./BTC_1h.csv"
btc_data = pd.read_csv(file_path)
btc_data = btc_data.rename(columns={
    'Open_time': 'datetime',
    '시가': 'open', '고가': 'high', '저가': 'low',
    '종가': 'close', '거래량': 'volume'
})
btc_data = btc_data[['datetime', 'open', 'high', 'low', 'close', 'volume']]
btc_data['datetime'] = pd.to_datetime(btc_data['datetime'])
btc_data.set_index('datetime', inplace=True)

class CustomData(bt.feeds.PandasData):
    params = (
        ('datetime', None), ('open', 'open'), ('high', 'high'),
        ('low', 'low'), ('close', 'close'), ('volume', 'volume'),
        ('openinterest', -1),
    )

data_feed = CustomData(dataname=btc_data)

class MACD_VXI_Enhanced(bt.Strategy):
    params = (('fast_length', 13), ('slow_length', 21), ('signal_length', 8),)

    def __init__(self):
        fast_ema = bt.ind.EMA(self.data.close, period=self.p.fast_length)
        slow_ema = bt.ind.EMA(self.data.close, period=self.p.slow_length)
        self.macd = fast_ema - slow_ema
        self.signal = bt.ind.SMA(self.macd, period=self.p.signal_length)
        self.hist = self.macd - self.signal
        self.logs = []

    def next(self):
        prev_macd, curr_macd = self.macd[-1], self.macd[0]
        prev_signal, curr_signal = self.signal[-1], self.signal[0]
        prev_hist, curr_hist = self.hist[-1], self.hist[0]
        strong = curr_signal >= curr_macd

        if prev_macd < prev_signal and curr_macd > curr_signal and curr_hist > prev_hist and strong and not self.position:
            self.buy()
            self.log(f"BUY: MACD↑ Signal + hist↑ + 강세 → MACD: {curr_macd:.4f}, Signal: {curr_signal:.4f}")

        elif prev_macd > prev_signal and curr_macd < curr_signal and curr_hist < prev_hist and not strong and self.position:
            self.close()
            self.log(f"SELL: MACD↓ Signal + hist↓ + 약세 → MACD: {curr_macd:.4f}, Signal: {curr_signal:.4f}")

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        log_entry = f"{dt.isoformat()} {txt}"
        print(log_entry)
        self.logs.append({'datetime': dt, 'log': txt})

    def stop(self):
        log_dir = "./log_dir"
        os.makedirs(log_dir, exist_ok=True)
        filename = "macd_vxi_enhanced_log.csv"
        pd.DataFrame(self.logs).to_csv(os.path.join(log_dir, filename), index=False)
        print(f"Trading log saved: {filename}")

# Cerebro 엔진 설정
cerebro = bt.Cerebro(optreturn=False, stdstats=False)
cerebro.broker.setcommission(commission=0.05 / 100, leverage=100)
cerebro.broker.setcash(10000)
cerebro.broker.set_coc(True)
cerebro.adddata(data_feed, name="BTC")
cerebro.addstrategy(MACD_VXI_Enhanced)
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

# 실행
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
print(f'\nFinal Portfolio Value: {cerebro.broker.getvalue()}')

# PyFolio 리포트
pyfoliozer = results[0].analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
qs.plots.snapshot(returns)

results_dir = "./results"
os.makedirs(results_dir, exist_ok=True)
report_filename = f"{results_dir}/MACD_VXI_Enhanced_{int(time.time())}.html"
qs.reports.html(returns, output=report_filename,
                download_filename=report_filename,
                title="MACD_VXI_Enhanced")
print(f"\n Report generated: {report_filename}")

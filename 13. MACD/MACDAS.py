import pandas as pd
import backtrader as bt
import time
import os
import quantstats as qs

# CSV 파일 경로 및 데이터 불러오기
file_path = "./BTC_1d.csv"
btc_data = pd.read_csv(file_path)

# 열 이름 변경: backtrader에서 사용하기 쉽도록 수정
btc_data = btc_data.rename(columns={
    'Open_time': 'datetime',
    '시가': 'open',
    '고가': 'high', 
    '저가': 'low',
    '종가': 'close',
    '거래량': 'volume'
})

# 필요한 컬럼만 선택 및 datetime 처리
btc_data = btc_data[['datetime', 'open', 'high', 'low', 'close', 'volume']]
btc_data['datetime'] = pd.to_datetime(btc_data['datetime'])
btc_data.set_index('datetime', inplace=True)

# 백트레이더 데이터피드로 변환
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

# Cerebro 엔진 초기 설정 및 브로커 설정
cerebro = bt.Cerebro(optreturn=False, stdstats=False)
cerebro.broker.setcommission(commission=0.05 / 100, leverage=100)  # upbit 수수료 0.05% 및 레버리지 100
cerebro.broker.setcash(10000) 
cerebro.broker.set_coc(True)  # 종가 진입

# 데이터 피드 추가
cerebro.adddata(data_feed, name="BTC")
class MACDAS_Strategy(bt.Strategy):
    params = (
        ('fast', 12),
        ('slow', 26),
        ('signal', 9),
    )

    def __init__(self):
        fast_ema = bt.ind.EMA(self.data.close, period=self.p.fast)
        slow_ema = bt.ind.EMA(self.data.close, period=self.p.slow)
        self.macd = fast_ema - slow_ema
        self.signal = bt.ind.EMA(self.macd, period=self.p.signal)

        self.macdas = self.macd - self.signal
        self.signalas = bt.ind.EMA(self.macdas, period=self.p.signal)

        self.logs = []

    def next(self):
        prev_macdas = self.macdas[-1]
        curr_macdas = self.macdas[0]
        prev_signalas = self.signalas[-1]
        curr_signalas = self.signalas[0]

        if prev_macdas < prev_signalas and curr_macdas > curr_signalas and not self.position:
            self.buy()
            self.log(f"BUY: MACDAS crossed above SignalAS → macdAS: {curr_macdas:.4f}, signalAS: {curr_signalas:.4f}")

        elif prev_macdas > prev_signalas and curr_macdas < curr_signalas and self.position:
            self.close()
            self.log(f"SELL: MACDAS crossed below SignalAS → macdAS: {curr_macdas:.4f}, signalAS: {curr_signalas:.4f}")

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")
        self.logs.append({'datetime': dt, 'log': txt})

    def stop(self):
        os.makedirs("./log_dir", exist_ok=True)
        df = pd.DataFrame(self.logs)
        df.to_csv("./log_dir/macdas_log.csv", index=False)
        print("Trading log saved: macdas_log.csv")

cerebro = bt.Cerebro(optreturn=False, stdstats=False)
cerebro.broker.setcommission(commission=0.05 / 100, leverage=100)
cerebro.broker.setcash(10000)
cerebro.broker.set_coc(True)
cerebro.adddata(data_feed, name="BTC")
cerebro.addstrategy(MACDAS_Strategy)
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
report_filename = f"{results_dir}/MACDAS_{int(time.time())}.html"
qs.reports.html(returns, output=report_filename,
                download_filename=report_filename,
                title="MACDAS")
print(f"\n Report generated: {report_filename}")

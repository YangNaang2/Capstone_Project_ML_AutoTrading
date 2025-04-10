
import pandas as pd
import backtrader as bt
import time
import os
import quantstats as qs

# CSV 파일 경로 및 데이터 불러오기
file_path = "./BTC_1h.csv"
btc_data = pd.read_csv(file_path)

# 열 이름 변경
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

# 백트레이더용 데이터 피드 정의
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

# 백테스트 엔진 설정
cerebro = bt.Cerebro(optreturn=False, stdstats=False)
cerebro.broker.setcommission(commission=0.05 / 100, leverage=100)
cerebro.broker.setcash(10000)
cerebro.broker.set_coc(True)
cerebro.adddata(data_feed, name="BTC")

class ExtremeMomentumReversal(bt.Strategy):
    params = dict(
        momentum_period=20,
        log=True,
        risk_ratio=10,  # 각 단계 매수 비율 = 전체 자금의 10%
        thresholds=[-1000, -2000, -4000, -8000],  # [-1000, -2000, ..., -10000]
        sell_threshold=5000,
    )

    def __init__(self):
        self.addminperiod(self.p.momentum_period * 2)

        self.mom = self.data.close - self.data.close(-self.p.momentum_period)
        self.mom_sma = bt.indicators.SimpleMovingAverage(self.mom, period=self.p.momentum_period)
        self.mom_hist = self.mom - self.mom_sma
        self.logs = []

        self.current_buy_level = -1  # 마지막으로 진입한 threshold 인덱스

    def next(self):
        curr_hist = self.mom_hist[0]

        # 🟥 매도 조건: 모멘텀이 반등하면 전량 매도
        if self.position and curr_hist > self.p.sell_threshold:
            self.log(f"[매도] 가격: {self.data.close[0]:.2f}, 수량: {self.position.size:.10f}")
            self.close()
            self.current_buy_level = -1  # 초기화
            return

        # 🟩 매수 조건: 새로운 threshold를 만족할 때만 추가 매수
        for i, threshold in enumerate(self.p.thresholds):
            if curr_hist < threshold and i > self.current_buy_level:
                order_size = self.broker.getcash() * self.p.risk_ratio / 100 / self.data.close[0]
                self.buy(size=order_size)
                self.log(f"[매수 {i+1}차] 모멘텀: {curr_hist:.2f}, 가격: {self.data.close[0]:.2f}, 수량: {order_size:.10f}")
                self.current_buy_level = i
                break  # 한 번에 한 단계만 매수

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        log_entry = f"{dt.isoformat()} {txt}"
        print(log_entry)
        self.logs.append({'datetime': dt, 'log': txt})

    def stop(self):
        log_dir = "./log_dir"
        os.makedirs(log_dir, exist_ok=True)
        filename = "trading_log.csv"
        df_logs = pd.DataFrame(self.logs)
        df_logs.to_csv(f"{log_dir}/{filename}", index=False)
        print(f"Trading log saved: {filename}")


# 전략 및 분석기 추가
cerebro.addstrategy(ExtremeMomentumReversal)
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

results = cerebro.run()

print(f'\nFinal Portfolio Value: {cerebro.broker.getvalue()}')

# 분석 결과 시각화 및 저장
pyfoliozer = results[0].analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
qs.plots.snapshot(returns)

results_dir = "./results"
os.makedirs(results_dir, exist_ok=True)
report_filename = f"{results_dir}/ExtremeMomentumReversal_{int(time.time())}.html"
qs.reports.html(returns, output=report_filename,
                download_filename=report_filename,
                title="Extreme Momentum Reversal Strategy")
print(f"\nReport generated: {report_filename}")
print("Complete")


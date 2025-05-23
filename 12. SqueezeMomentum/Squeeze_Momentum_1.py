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

# 스퀴즈 모멘텀 전략 (모멘텀 반전 기준 진입/청산)
class SqueezeMomentumStrategy(bt.Strategy):
    params = dict(
        bb_period=20,           # 볼린저 밴드 기간
        bb_dev=2.0,             # 볼린저 밴드 표준편차 배수
        kc_period=20,           # 켈트너 채널 계산 기간 (SMA, ATR)
        kc_atr_multiplier=1.5,  # 켈트너 채널 ATR 배수
        momentum_period=20,     # 모멘텀 계산 기간
        log=True,
        risk_ratio=100,         # 위험 비율
    )

    def __init__(self):
        self.addminperiod(max(self.p.bb_period, self.p.kc_period, self.p.momentum_period * 2))

        self.boll = bt.indicators.BollingerBands(
            self.data.close, period=self.p.bb_period, devfactor=self.p.bb_dev
        )

        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.kc_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.kc_period)
        self.upper_kc = self.sma + self.p.kc_atr_multiplier * self.atr
        self.lower_kc = self.sma - self.p.kc_atr_multiplier * self.atr

        self.mom = self.data.close - self.data.close(-self.p.momentum_period)
        self.mom_sma = bt.indicators.SimpleMovingAverage(self.mom, period=self.p.momentum_period)
        self.mom_hist = self.mom - self.mom_sma

        self.logs = []

    def next(self):
        if len(self) < 2:
            return

        prev_hist = self.mom_hist[-1]
        curr_hist = self.mom_hist[0]

        if not self.position:
            if prev_hist < 0 and curr_hist > 0:
                order_size = self.broker.getcash() * self.p.risk_ratio / 100 / self.data.close[0]
                self.buy(size=order_size)
                self.log(f"[매수] 가격: {self.data.close[0]:.2f}, 수량: {order_size:.10f}")

        elif self.position.size > 0:
            if prev_hist > 0 and curr_hist < 0:
                self.close()
                self.log(f"[매도] 가격: {self.data.close[0]:.2f}, 수량: {self.position.size:.10f}")

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        log_entry = f"{dt.isoformat()} {txt}"
        print(log_entry)
        self.logs.append({'datetime': dt, 'log': txt})

    def stop(self):
        log_dir = "./log_dir"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        filename = f"trading_log.csv"
        df_logs = pd.DataFrame(self.logs)
        df_logs.to_csv(f"{log_dir}/{filename}", index=False)
        print(f"Trading log saved: {filename}")

# 전략 추가
cerebro.addstrategy(SqueezeMomentumStrategy)

# PyFolio 분석기 추가
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

# 백테스트 시작 전 포트폴리오 값 출력
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# 백테스트 실행
results = cerebro.run()

# 최종 포트폴리오 값 출력
print(f'\nFinal Portfolio Value: {cerebro.broker.getvalue()}')

# PyFolio 분석 결과 획득 및 시각화
pyfoliozer = results[0].analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
qs.plots.snapshot(returns)

# 결과 리포트 생성
results_dir = "./results"
if not os.path.exists(results_dir):
    os.makedirs(results_dir)
report_filename = f"{results_dir}/SqueezeMomentum_{int(time.time())}.html"
qs.reports.html(returns, output=report_filename,
                download_filename=report_filename,
                title="Squeeze Momentum Strategy")
print(f"\nReport generated: {report_filename}")
print("Complete")

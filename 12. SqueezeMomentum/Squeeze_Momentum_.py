# 롱 숏 손익비

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
cerebro.broker.setcash(100_0000) 
cerebro.broker.set_coc(True)  # 종가 진입

# 데이터 피드 추가
cerebro.adddata(data_feed, name="BTC")

# 스퀴즈 모멘텀 전략 구현
class SqueezeMomentumStrategy(bt.Strategy):
    params = dict(
        bb_period=20,           # 볼린저 밴드 기간
        bb_dev=2.0,             # 볼린저 밴드 표준편차 배수
        kc_period=20,           # 켈트너 채널 계산 기간 (SMA, ATR)
        kc_atr_multiplier=1.5,  # 켈트너 채널 ATR 배수
        momentum_period=20,     # 모멘텀 계산 기간
        atr_multiplier=1.5,     # 진입 후 손절/익절에 사용할 ATR 배수
        log=True,
    )

    def __init__(self):
        # 충분한 데이터 확보를 위해 최소 기간 설정
        self.addminperiod(max(self.p.bb_period, self.p.kc_period, self.p.momentum_period * 2))
        
        # 볼린저 밴드 계산 (내부에 top, mid, bot 라인이 생성됨)
        self.boll = bt.indicators.BollingerBands(
            self.data.close, period=self.p.bb_period, devfactor=self.p.bb_dev
        )
        
        # 켈트너 채널 계산: 단순 이동평균(SMA)와 ATR 기반 상/하 채널
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.kc_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.kc_period)
        self.upper_kc = self.sma + self.p.kc_atr_multiplier * self.atr
        self.lower_kc = self.sma - self.p.kc_atr_multiplier * self.atr
        
        # 모멘텀 히스토그램 계산
        # 모멘텀 = 현재 종가 - momentum_period 전 종가
        self.mom = self.data.close - self.data.close(-self.p.momentum_period)
        # 모멘텀의 단순 이동평균
        self.mom_sma = bt.indicators.SimpleMovingAverage(self.mom, period=self.p.momentum_period)
        # 모멘텀 히스토그램 = 모멘텀 - 모멘텀의 이동평균
        self.mom_hist = self.mom - self.mom_sma

        # 진입 시점의 가격과 손절/익절 가격을 저장할 변수
        self.entry_price = None
        self.sl = None
        self.tp = None

    def next(self):
        # 스퀴즈 조건: 볼린저 밴드가 켈트너 채널 내부에 있으면 squeeze_on = True
        squeeze_on = (self.boll.bot[0] > self.lower_kc[0]) and (self.boll.top[0] < self.upper_kc[0])
        
        # 포지션이 없을 때 진입 조건 체크
        if not self.position:
            # 이전 바와 현재 바의 모멘텀 히스토그램 값으로 제로크로스 판단
            if len(self) > 1:
                prev_hist = self.mom_hist[-1]
                curr_hist = self.mom_hist[0]
                # 스퀴즈 해제 상태에서, 음에서 양으로 전환하면 롱 진입
                if (prev_hist < 0 and curr_hist > 0) and (not squeeze_on):
                    self.buy()
                    self.entry_price = self.data.close[0]
                    self.sl = self.entry_price - self.p.atr_multiplier * self.atr[0]
                    self.tp = self.entry_price + self.p.atr_multiplier * self.atr[0]
                    if self.p.log:
                        self.log(f"[Long 진입] 가격: {self.entry_price:.2f}, SL: {self.sl:.2f}, TP: {self.tp:.2f}")
                # 스퀴즈 해제 상태에서, 양에서 음으로 전환하면 숏 진입
                elif (prev_hist > 0 and curr_hist < 0) and (not squeeze_on):
                    self.sell()
                    self.entry_price = self.data.close[0]
                    self.sl = self.entry_price + self.p.atr_multiplier * self.atr[0]
                    self.tp = self.entry_price - self.p.atr_multiplier * self.atr[0]
                    if self.p.log:
                        self.log(f"[Short 진입] 가격: {self.entry_price:.2f}, SL: {self.sl:.2f}, TP: {self.tp:.2f}")
        else:
            # 포지션 보유 중일 때, 손절/익절 조건 확인
            # 롱 포지션인 경우: 현재 최저가가 SL에 도달하거나 현재 최고가가 TP에 도달하면 청산
            if self.position.size > 0:
                if self.data.low[0] <= self.sl or self.data.high[0] >= self.tp:
                    exit_price = self.sl if self.data.low[0] <= self.sl else self.tp
                    self.close()
                    if self.p.log:
                        self.log(f"[Long 청산] 가격: {exit_price:.2f}")
            # 숏 포지션인 경우: 현재 최고가가 SL에 도달하거나 현재 최저가가 TP에 도달하면 청산
            elif self.position.size < 0:
                if self.data.high[0] >= self.sl or self.data.low[0] <= self.tp:
                    exit_price = self.sl if self.data.high[0] >= self.sl else self.tp
                    self.close()
                    if self.p.log:
                        self.log(f"[Short 청산] 가격: {exit_price:.2f}")

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

# 전략 추가
cerebro.addstrategy(SqueezeMomentumStrategy)

# PyFolio 분석기 추가
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

# 백테스트 시작 전 포트폴리오 값 출력
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# 백테스트 실행
results = cerebro.run()

# 최종 포트폴리오 값 출력
final_value = cerebro.broker.getvalue()
print(f'\nFinal Portfolio Value: {final_value:.2f}')

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

# main.py
import pandas as pd
import backtrader as bt
import datetime
import time

# CSV 파일 경로
file_path = "./Recent_BTC_1day.csv"

# CSV 파일을 pandas 데이터프레임으로 불러오기
btc_data = pd.read_csv(file_path)

# 열 이름을 backtrader에서 사용하기 쉽게 변경
btc_data = btc_data.rename(columns={
    'Open_time': 'datetime',
    '시가': 'open',
    '고가': 'high',
    '저가': 'low',
    '종가': 'close',
    '거래량': 'volume'
})

# backtrader에 필요 없는 열 제거
btc_data = btc_data[['datetime', 'open', 'high', 'low', 'close', 'volume']]

# datetime 컬럼을 datetime 타입으로 변환하고 인덱스로 설정
btc_data['datetime'] = pd.to_datetime(btc_data['datetime'])
btc_data.set_index('datetime', inplace=True)

# backtrader 데이터피드로 변환
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

# Cerebro 초기 설정 및 데이터 추가
cerebro = bt.Cerebro(optreturn=False, stdstats=False)  # 최적화를 위한 옵션 설정
cerebro.broker.setcommission(commission=0.05 / 100, leverage=100)  # upbit 수수료인 0.05% 수수료 설정
cerebro.broker.setcash(10_000_000)
cerebro.broker.set_coc(True)  # 종가 진입 설정

# 데이터 피드 추가
cerebro.adddata(data_feed, name="BTC")

# 전략 클래스 정의
class MovingAverageCrossStrategy(bt.Strategy):
    params = dict(
        log=True,  # 로그 출력을 위한 설정 변경
        risk_ratio=10  # 위험 비율 (포트폴리오 대비 주문 규모)
    )

    def log(self, txt, dt=None):
        '''로깅 기능 (날짜 포함)'''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        self.sma_short = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=10)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=50)

    def next(self):
        # 현재 보유 상태 확인
        if not self.position:  # 포지션이 없는 경우
            if self.sma_short[0] > self.sma_long[0]:  # 골든크로스 (매수 신호)
                cash = self.broker.getcash()
                size = (cash / self.datas[0].close[0]) * (self.p.risk_ratio / 100)
                self.buy(size=size)
                if self.p.log:
                    self.log(f'[매수 신호] 가격: {self.datas[0].close[0]:.2f}, 수량: {size:.6f}')
        else:  # 포지션이 있는 경우
            if self.sma_short[0] < self.sma_long[0]:  # 데드크로스 (매도 신호)
                self.sell(size=self.position.size)
                if self.p.log:
                    self.log(f'[매도 신호] 가격: {self.datas[0].close[0]:.2f}, 수량: {self.position.size:.6f}')

# 전략 추가
cerebro.addstrategy(MovingAverageCrossStrategy)
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')  # 결과 분석 추가

# 백테스트 실행
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

results = cerebro.run()
pyfoliozer = results[0].analyzers.getbyname('pyfolio')

# 결과 처리
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
returns.index = returns.index.tz_convert(None)

print(f'\nFinal Portfolio Value {cerebro.broker.getvalue()}')

# 수익률 시각화 및 보고서 생성
import quantstats as qs
qs.plots.snapshot(returns)

print("\nGenerating report...")
import os
if not os.path.exists("./results"):
    os.makedirs("./results")
qs.reports.html(returns, output=f'./results/MovingAverageCross_10_50.html',
                download_filename=f'./results/MovingAverageCross_10_50.html',
                title="Moving Average Cross Strategy")
print("Complete")
import pandas as pd
import backtrader as bt
import time
import numpy as np
from sklearn.linear_model import LinearRegression
import os
import quantstats as qs

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
cerebro = bt.Cerebro(optreturn=False, stdstats=False)
cerebro.broker.setcommission(commission=0.05 / 100, leverage=100)  # upbit 수수료 설정
cerebro.broker.setcash(10_000)  # 초기 자본
cerebro.broker.set_coc(True)  # 종가 진입 설정

# 데이터 피드 추가
cerebro.adddata(data_feed, name="BTC")

# 선형회귀 전략 클래스
class LinearRegressionStrategy(bt.Strategy):
    params = dict(
        window=14,  # 선형회귀를 계산할 윈도우 크기
        log=True,   # 로그 출력 여부
        risk_ratio=10  # 위험 비율 (포트폴리오 대비 주문 규모)
    )

    def log(self, txt, dt=None):
        '''로깅 기능 (날짜 포함)'''
        dt = dt or self.datas[0].datetime.date(0)
        if self.p.log:
            print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        self.lr_model = LinearRegression()
        self.close_prices = []  # 종가를 저장할 리스트

    def next(self):
        # 현재 종가를 저장
        self.close_prices.append(self.data.close[0])
        
        # 윈도우 길이 이상의 데이터가 있어야 선형회귀 계산 가능
        if len(self.close_prices) >= self.p.window:
            # 윈도우 크기만큼 데이터를 슬라이싱
            y = np.array(self.close_prices[-self.p.window:])
            X = np.arange(len(y)).reshape(-1, 1)  # 날짜를 X로 사용
            
            # 선형회귀 모델 학습
            self.lr_model.fit(X, y)
            slope = self.lr_model.coef_[0]  # 기울기 (상승/하락 추세)
            intercept = self.lr_model.intercept_  # 절편

            # 현재 가격과 예측 가격
            current_price = self.data.close[0]
            predicted_price = slope * len(y) + intercept
            
            # 매수/매도 시그널 생성
            if slope > 0 and not self.position:  # 상승 추세에서 매수
                order_size = self.broker.getvalue() * (self.p.risk_ratio / 100) / current_price
                self.buy(size=order_size)
                self.log(f"[매수 시그널] 가격: {current_price:.2f}, 예측 가격: {predicted_price:.2f}, 수량: {order_size:.10f}")

            elif slope < 0 and self.position:  # 하락 추세에서 매도
                self.sell(size=self.position.size)
                self.log(f"[매도 시그널] 가격: {current_price:.2f}, 예측 가격: {predicted_price:.2f}, 수량: {self.position.size:.10f}")

# Cerebro 설정 및 전략 추가
cerebro.addstrategy(LinearRegressionStrategy, window=14)
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

# 백테스트 실행
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
pyfoliozer = results[0].analyzers.pyfolio

# 결과 처리 및 시각화
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
returns.index = returns.index.tz_convert(None)

# 결과 출력
print(f'\nFinal Portfolio Value {cerebro.broker.getvalue()}')

# 결과 디렉토리 확인 및 생성
if not os.path.exists("./results"):
    os.makedirs("./results")

# QuantStats 시각화 및 보고서 생성
qs.plots.snapshot(returns)
qs.reports.html(
    returns, 
    output=f'./results/LinearRegressionStrategy_{int(time.time())}.html'
)

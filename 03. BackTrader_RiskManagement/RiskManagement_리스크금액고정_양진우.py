import backtrader as bt
import yfinance as yf
import math
import quantstats as qs
import pandas as pd

# Bollinger Bands 전략 클래스
class BollingerBandsStrategy(bt.Strategy):
    params = dict(
        ma_period=50,         # 이동평균 기간
        dev_factor=1,         # 표준편차 계수
        risk_ratio=0.02,      # 리스크 비율 (2%)
        stop_loss_ratio=0.01  # 손절 비율 (1%)
    )

    def __init__(self):
        self.bbands = bt.ind.BollingerBands(period=self.p.ma_period, devfactor=self.p.dev_factor)
        self.order = None  # 주문 상태
        self.stop_loss_price = None  # 손절가

    def next(self):
        # 손절가 체크
        if self.position:
            if self.data.close[0] <= self.stop_loss_price:  # 손절가에 도달했는지 확인
                self.order = self.sell(size=self.position.size)  # 매도 (손절)
                print(f"Stop Loss triggered: Sold {self.position.size} shares at {self.data.close[0]:.2f}")
                self.stop_loss_price = None  # 손절가 초기화
                return  # 손절 후 더 이상 진행하지 않음

        if not self.position:  # 포지션이 없을 때
            if self.data.close[0] < self.bbands.lines.bot[0]:  # 하단 밴드 아래
                # 매수 금액 계산
                total_capital = self.broker.getvalue()  # 총 자본
                risk_amount = total_capital * self.p.risk_ratio  # 리스크 금액
                stop_loss_distance = self.data.close[0] * self.p.stop_loss_ratio  # 손절가 거리
                order_size = math.floor(risk_amount / stop_loss_distance)  # 매수 사이즈

                self.order = self.buy(size=order_size)  # 매수
                self.stop_loss_price = self.data.close[0] * (1 - self.p.stop_loss_ratio)  # 손절가 설정

                print(f"Buy Order: {order_size} shares at {self.data.close[0]:.2f}, "
                      f"Stop Loss set at {self.stop_loss_price:.2f}")

        elif self.data.close[0] > self.bbands.lines.top[0]:  # 상단 밴드 위
            self.order = self.sell(size=self.position.size)  # 매도
            print(f"Sell Order: {self.position.size} shares at {self.data.close[0]:.2f}")

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)  # 초기 자본 설정

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # 데이터 피드 생성
    data = bt.feeds.PandasData(dataname=yf.download('MSFT', '2011-01-01', '2013-12-31'))
    cerebro.adddata(data)  # 데이터 피드 추가

    # 전략 추가
    cerebro.addstrategy(BollingerBandsStrategy)

    # 백테스트 실행
    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # 백트레이더 결과를 얻기 위한 필수 처리
    strat = cerebro.run()[0]
    portfolio_value = cerebro.broker.getvalue()
    returns = cerebro.broker.get_value() - 100000  # 수익률 계산

    # 퀀트스탯 활용
    # 데이터를 리스트로 변환하여 수익률 분석
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')
    strat = cerebro.run()[0]
    analyzer = strat.analyzers.getbyname('returns')
    returns = analyzer.get_analysis()

    # 수익률 데이터를 시리즈로 변환
    returns_series = pd.Series(returns)

    # Quantstats 리포트 생성
    qs.reports.html(returns_series, "strategy_analysis.html")

    # Quantstats 그래프 출력
    qs.plots.snapshot(returns_series, title="Bollinger Bands Strategy Performance")

import backtrader as bt
import yfinance as yf
import math

class FixedTradeCountStrategy(bt.Strategy):
    params = dict(
        max_trades=5,  # 최대 매매 횟수
        initial_cash=100000.0  # 가상의 초기 자본
    )

    def __init__(self):
        self.trade_count = 0  # 매매 횟수 카운터
        self.trade_amount = self.p.initial_cash / self.p.max_trades  # 회당 투자 금액

    def next(self):
        # 매매 횟수가 남아있을 때만 실행
        if self.trade_count < self.p.max_trades:
            order_size = math.floor(self.trade_amount / self.data.close[0])  # 매수 가능한 수량 계산
            if not self.position:  # 포지션이 없을 때 매수
                self.buy(size=order_size)
                self.trade_count += 1  # 매매 횟수 증가
            elif self.position.size > 0:  # 포지션이 있을 때 매도
                self.sell(size=self.position.size)

# 전략 실행
if __name__ == '__main__':
    # Yahoo Finance에서 데이터 다운로드
    data = bt.feeds.PandasData(dataname=yf.download('MSFT', '2011-01-01', '2013-12-31'))

    # 초기 자본 설정
    initial_cash = 100000.0

    # Cerebro 초기화 및 전략 설정
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.adddata(data)
    cerebro.addstrategy(FixedTradeCountStrategy)
    
    # 실행 및 결과 출력
    cerebro.run()
    final_value = cerebro.broker.getvalue()
    
    print(f"최종 자본: {final_value:.2f}")
    print(f"수익률: {((final_value - initial_cash) / initial_cash) * 100:.2f}%")

import yfinance as yf
import datetime
import backtrader as bt
import math
import quantstats as qs

# RSI 전략
class RSI(bt.Strategy):
    params = dict(
        rsi_period=14,   # RSI 기간 설정
        rsi_low=25,      # RSI 낮은 값 (과매도 구간)
        rsi_high=75,     # RSI 높은 값 (과매수 구간)
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=self.p.rsi_period)

    def next(self):
        if self.getposition().size == 0:  # 포지션이 없을 경우
            if self.rsi < self.p.rsi_low:  # RSI가 과매도 구간보다 낮으면 매수
                order_size = math.floor(self.broker.get_cash() / self.data.close[0] / 2 * 0.99)
                self.buy(size=order_size)  # 롱 포지션 진입
        elif self.rsi > self.p.rsi_high:  # RSI가 과매수 구간보다 높으면 청산
            self.close()  # 포지션 종료

    def log(self, message):
        print(message)
                
    def notify_order(self, order):
        if order.status in [order.Completed]:
            cur_date = order.data.datetime.date(0)
            if order.isbuy():
                self.log(f'{cur_date} [매수 주문 실행] 수량: {order.size} 가격: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'{cur_date} [매도 주문 실행] 수량: {order.size} 가격: {order.executed.price:.2f}')

if __name__ == '__main__':
    # Cerebro 초기화 및 설정
    cerebro = bt.Cerebro() 
    cerebro.broker.setcommission(commission=0.003)  # 0.3% 수수료 설정
    cerebro.broker.setcash(10_000_000)  # 시작 자본금 설정

    print('시작 포트폴리오 가격: %.2f' % cerebro.broker.getvalue())

    # Yahoo Finance에서 삼성전자 주식 데이터를 가져옴
    start_date = datetime.datetime(2020, 1, 1)  # 원하는 시작 날짜
    end_date = datetime.datetime(2023, 1, 1)    # 원하는 종료 날짜
    data = yf.download('005930.KS', start=start_date, end=end_date)

    # backtrader에 맞게 데이터 변환
    data_bt = bt.feeds.PandasData(dataname=data)

    # 데이터 추가
    cerebro.adddata(data_bt)

    # 전략 추가
    cerebro.addstrategy(RSI)

    # 분석 도구 추가
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    # 실행
    results = cerebro.run()
    print('끝 포트폴리오 가격: %.2f' % cerebro.broker.getvalue())

    # 분석 결과 출력
    strat = results[0]
    pyfoliozer = strat.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
    returns.index = returns.index.tz_convert(None)

    # 결과 요약 출력
    cagr = qs.stats.cagr(returns)
    mdd = qs.stats.max_drawdown(returns)
    sharpe = qs.stats.sharpe(returns)
    print(f"SHARPE: {sharpe:.2f}")
    print(f"CAGR: {cagr * 100:.2f} %")
    print(f"MDD : {mdd * 100:.2f} %")

    # 결과를 HTML 파일로 저장
    df = yf.download('005930.KS', start=start_date, end=end_date)
    qs.reports.html(returns, benchmark=df['Close'], output='RSI_1stock_result.html', title='RSI 전략 결과')

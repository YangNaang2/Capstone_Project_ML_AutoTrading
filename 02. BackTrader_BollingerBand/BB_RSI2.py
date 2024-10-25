from datetime import datetime, timedelta
import backtrader as bt
import math
import quantstats as qs
import pandas as pd
import yfinance as yf

# 사용자로부터 주식 코드 입력받기
stock_code = input("주식 코드를 입력하세요 (예: MSFT): ")

# 볼린저 밴드 + RSI 전략
class BollingerBandsRSI(bt.Strategy):
    params = dict(
        period=20,    # 볼린저 밴드 기간
        devfactor=2.0, # 표준편차 계수
        rsi_period=14, # RSI 기간
        rsi_low=30,    # RSI 저점 (매수)
        rsi_high=90    # RSI 고점 (매도)
    )

    def __init__(self):
        # 볼린저 밴드와 RSI 초기화
        self.bb = bt.indicators.BollingerBands(period=self.params.period, devfactor=self.params.devfactor)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)
    
    def next(self):
        if not self.position:  # 포지션이 없을 경우
            # 주가가 하단 밴드보다 낮거나 RSI가 30보다 낮으면 매수 
            if self.data.close[0] < self.bb.lines.bot[0] or self.rsi[0] < self.params.rsi_low:
                order_size = math.floor(self.broker.get_value() / self.datas[0].close)
                self.buy(size=order_size)
        else:
            # 주가가 상단 밴드보다 높고 RSI가 80보다 높으면 매도 
            if self.data.close[0] > self.bb.lines.top[0] or self.rsi[0] > self.params.rsi_high:
                self.close()

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10000.0)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # 오늘 날짜와 10년 전 날짜 계산
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*10)

    # 데이터 피드 생성
    data = bt.feeds.PandasData(dataname=yf.download(stock_code, start=start_date, end=end_date))

    cerebro.adddata(data)  # 데이터 피드 추가
    cerebro.addstrategy(BollingerBandsRSI)  # 볼린저 밴드 + RSI 전략 추가
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')  # 결과 분석 추가

    results = cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    strat = results[0]
    pyfoliozer = strat.analyzers.getbyname('pyfolio')

    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
    returns.index = returns.index.tz_convert(None)
    
    # 벤치마크 데이터 생성 (예: S&P 500 지수)
    benchmark_data = yf.download('^GSPC', start=start_date, end=end_date)['Adj Close']
    
    # 간단한 결과 출력
    print(f'\n')
    print("Result:")
    cagr = qs.stats.cagr(returns)
    mdd = qs.stats.max_drawdown(returns)
    sharpe = qs.stats.sharpe(returns)
    print(f"SHARPE: {sharpe:.2f}")
    print(f"CAGR: {cagr * 100:.2f} %")
    print(f"MDD : {mdd * 100:.2f} %")
    
    # 자세한 결과 html 파일로 저장 (주식 코드 포함)
    qs.reports.html(returns, benchmark=benchmark_data, output=f'BollingerBandsRSI_{stock_code}.html', title=f'Bollinger Bands + RSI Strategy Results for {stock_code}')
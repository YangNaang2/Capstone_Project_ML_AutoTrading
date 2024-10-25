#1년에 10번을 매매가능 횟수를 정함, RSI 90일 때 매도

from datetime import datetime
import backtrader as bt
import quantstats as qs
import yfinance as yt
import time
import os

symbol = input("주식 코드를 입력해 주세요 :")

def collect_tick(symbol, timeframe="1d"):
    if not os.path.exists("./data"):
        os.makedirs("./data")
    time.sleep(1)
    df = yt.download(symbol, "1900-01-01")
    if df.shape[0] == 0:
        print(f"{symbol} ERROR: No Data!!!")
        exit(0)
    file_name = f"./data/{symbol}_{timeframe}_tick.csv"
    print(file_name, "->", df.head(1).index.values[0], "~", df.tail(1).index.values[0])
    print("=" * 10)
    df = df[['Open', 'High', 'Low', 'Adj Close', 'Volume']]
    df.to_csv(file_name, mode='w', header=False, date_format='%Y-%m-%dT%H:%M:%SZ')


class BollingerBandRSILimitedTrades(bt.Strategy):
    params = dict(
        log=False,
        options=None,
        max_trades_per_year=10  # 연간 최대 매매 횟수
    )

    def __init__(self):
        self.risk_ratio = 10
        self.bband = bt.indicators.BBands(self.datas[0], period=80, devfactor=1)
        self.rsi = bt.indicators.RSI(self.datas[0], period=14)
        self.trade_count = 0
        self.current_year = self.data.datetime.date(0).year

    def next(self):
        # 연도가 바뀌면 매매 횟수 초기화
        if self.current_year != self.data.datetime.date(0).year:
            self.current_year = self.data.datetime.date(0).year
            self.trade_count = 0

        # 매매 횟수 제한을 초과한 경우 매매하지 않음
        if self.trade_count >= self.p.max_trades_per_year:
            return

        top_band = self.bband.top[0]
        mid_band = self.bband.mid[0]

        # 매수 조건: 종가가 상단 밴드를 넘었을 때
        if top_band < self.datas[0].close[0] and self.getposition(self.datas[0]).size == 0:
            order_amount = (self.broker.get_value() * self.risk_ratio / 100) / (self.datas[0].close[0] - mid_band)
            self.buy(data=self.datas[0], size=order_amount)
            self.trade_count += 1  # 매수 시 매매 횟수 증가

        # 매도 조건: 중간 밴드보다 가격이 낮거나 RSI가 90 이상일 때
        if (mid_band > self.datas[0].close[0] or self.rsi[0] > 90) and self.getposition(self.datas[0]).size > 0:
            self.sell(data=self.datas[0], size=self.getposition(self.datas[0]).size)
            self.trade_count += 1  # 매도 시 매매 횟수 증가

    def log(self, message):
        if self.p.log:
            print(message)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        cur_date = order.data.datetime.date(0)
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'{cur_date} [매수 주문] 종목: {order.data._name} \t 수량: {order.size} \t 가격: {order.executed.price:.4f}')
            elif order.issell():
                self.log(f'{cur_date} [매도 주문] 종목: {order.data._name} \t 수량: {order.size} \t 가격: {order.executed.price:.4f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'{cur_date} {order.status} 주문 거부됨: 종목: {order.data._name} \t 수량: {order.size} \t 가격: {order.executed.price:.4f}')
            self.log("!Error: Order Rejected")
            exit(1)


# 1일봉 만들기
class SymbolData1d(bt.feeds.GenericCSVData):
    params = (
        ('timeframe', bt.TimeFrame.Days),
        ('compression', 1),
        ('dtformat', '%Y-%m-%dT%H:%M:%SZ'),
        ('fromdate', datetime(2004, 1, 1, 0, 0, 0)),
        ('datetime', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', -1)
    )


if __name__ == '__main__':
    cerebro = bt.Cerebro(optreturn=False, stdstats=False)
    cerebro.broker.setcommission(commission=0.2 / 100, leverage=100)
    cerebro.broker.setcash(10_000_000)
    cerebro.broker.set_coc(True)

    options = {
        symbol: {},
    }

    for v in options.keys():
        collect_tick(v, "1d")

    timeframe = "1d"

    for kind in options:
        for ts in [timeframe]:
            tick_path = f"./data/{kind}_{ts}_tick.csv"
            cryptoDataFeed = locals()[f"SymbolData{ts}"](dataname=tick_path)
            data_name = tick_path.split("/")[-1].split(".")[0]
            cerebro.adddata(cryptoDataFeed, name=data_name)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.addstrategy(BollingerBandRSILimitedTrades, log=True)
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    results = cerebro.run()
    pyfoliozer = results[0].analyzers.getbyname('pyfolio')

    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
    returns.index = returns.index.tz_convert(None)

    print(f'\nFinal Portfolio Value {cerebro.broker.getvalue()}')
    qs.plots.snapshot(returns)

    print("\nGenerating report...")
    if not os.path.exists("./results"):
        os.makedirs("./results")
    qs.reports.html(returns, output=f'./results/BollingerBandRSILimitedTrades_{int(time.time())}.html',
                    download_filename=f'./results/BollingerBandRSILimitedTrades_{int(time.time())}.html',
                    title="BollingerBandRSILimitedTrades")
    print("Complete")

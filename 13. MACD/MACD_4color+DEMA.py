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
                
class MACD_DEMA_4Color(bt.Strategy):
    params = (
        ('sma', 12),
        ('lma', 26),
        ('signal', 9),
    )

    def __init__(self):
        # DEMA 구성
        ema_fast = bt.ind.EMA(self.data.close, period=self.p.sma)
        ema_fast_2 = bt.ind.EMA(ema_fast, period=self.p.sma)
        self.dema_fast = (2 * ema_fast) - ema_fast_2

        ema_slow = bt.ind.EMA(self.data.close, period=self.p.lma)
        ema_slow_2 = bt.ind.EMA(ema_slow, period=self.p.lma)
        self.dema_slow = (2 * ema_slow) - ema_slow_2

        self.macd_dema = self.dema_fast - self.dema_slow

        # Signal line (DEMA 기준)
        signal_ema = bt.ind.EMA(self.macd_dema, period=self.p.signal)
        signal_ema_2 = bt.ind.EMA(signal_ema, period=self.p.signal)
        self.signal_dema = (2 * signal_ema) - signal_ema_2

        # 4Color MACD용 기본 MACD 선
        self.macd = bt.ind.MACD(self.data.close,
                                period_me1=self.p.sma,
                                period_me2=self.p.lma,
                                period_signal=self.p.signal)

        self.logs = []

    def next(self):
        curr_macd_dema = self.macd_dema[0]
        curr_signal_dema = self.signal_dema[0]
        curr_macd = self.macd.macd[0]
        prev_macd = self.macd.macd[-1]

        if (
            curr_macd_dema > curr_signal_dema and
            curr_macd > 0 and
            curr_macd > prev_macd and
            not self.position
        ):
            self.buy()
            self.log(f"BUY: MACD_DEMA > Signal_DEMA and MACD 상승")

        elif (
            (curr_macd_dema < curr_signal_dema or curr_macd < prev_macd)
            and self.position
        ):
            self.close()
            self.log(f"SELL: MACD_DEMA < Signal_DEMA or MACD 하락")

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")
        self.logs.append({'datetime': dt, 'log': txt})

    def stop(self):
        os.makedirs('./log_dir', exist_ok=True)
        pd.DataFrame(self.logs).to_csv('./log_dir/macd_dema_4color_log.csv', index=False)

cerebro.addstrategy(MACD_DEMA_4Color)

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
report_filename = f"{results_dir}/MACD_4Color_DEMA_{int(time.time())}.html"
qs.reports.html(returns, output=report_filename,
                download_filename=report_filename,
                title="MACD_4Color_DEMA")
print(f"\nReport generated: {report_filename}")
print("Complete")

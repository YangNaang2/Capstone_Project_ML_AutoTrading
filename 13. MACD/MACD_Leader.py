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
class MACDLeaderStrategy(bt.Strategy):
    params = (
        ('short_length', 12),
        ('long_length', 26),
        ('sig_length', 9),
    )

    def __init__(self):
        src = self.data.close
        # 선행 MACD 구성
        sema = bt.ind.EMA(src, period=self.p.short_length)
        lema = bt.ind.EMA(src, period=self.p.long_length)
        self.i1 = sema + bt.ind.EMA(src - sema, period=self.p.short_length)
        self.i2 = lema + bt.ind.EMA(src - lema, period=self.p.long_length)
        self.macdl = self.i1 - self.i2  # MACD Leader
        self.logs = []

    def next(self):
        prev = self.macdl[-1]
        curr = self.macdl[0]

        # 매수 조건: MACDL이 0선을 상향 돌파
        if prev < 0 and curr > 0 and not self.position:
            self.buy()
            self.log(f"BUY: MACDL crossed above 0 → MACDL: {curr:.4f}")

        # 매도 조건: MACDL이 0선을 하향 돌파
        elif prev > 0 and curr < 0 and self.position:
            self.close()
            self.log(f"SELL: MACDL crossed below 0 → MACDL: {curr:.4f}")

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")
        self.logs.append({'datetime': dt, 'log': txt})

    def stop(self):
        log_dir = "./log_dir"
        os.makedirs(log_dir, exist_ok=True)
        df = pd.DataFrame(self.logs)
        df.to_csv(os.path.join(log_dir, "macd_leader_log.csv"), index=False)
        print("📄 Trading log saved.")

cerebro.addstrategy(MACDLeaderStrategy)

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
report_filename = f"{results_dir}/MACD_Leader_{int(time.time())}.html"
qs.reports.html(returns, output=report_filename,
                download_filename=report_filename,
                title="MACD_Leader")
print(f"\nReport generated: {report_filename}")
print("Complete")

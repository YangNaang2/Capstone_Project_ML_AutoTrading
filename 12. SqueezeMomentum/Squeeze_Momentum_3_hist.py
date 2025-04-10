import pandas as pd
import matplotlib.pyplot as plt

# 데이터 불러오기 및 전처리
btc_df = pd.read_csv("BTC_1h.csv")
btc_df = btc_df.rename(columns={
    'Open_time': 'datetime',
    '시가': 'open',
    '고가': 'high',
    '저가': 'low',
    '종가': 'close',
    '거래량': 'volume'
})
btc_df['datetime'] = pd.to_datetime(btc_df['datetime'])
btc_df.set_index('datetime', inplace=True)

# 모멘텀 히스토그램 계산
momentum_period = 20
btc_df['momentum'] = btc_df['close'] - btc_df['close'].shift(momentum_period)
btc_df['mom_sma'] = btc_df['momentum'].rolling(momentum_period).mean()
btc_df['mom_hist'] = btc_df['momentum'] - btc_df['mom_sma']

# 1000 단위 구간화
bins = list(range(-10000, 11000, 1000))
labels = [f"{i} ~ {i+1000}" for i in bins[:-1]]
btc_df['hist_bin'] = pd.cut(btc_df['mom_hist'], bins=bins, labels=labels)

# 각 구간 빈도 계산
hist_counts = btc_df['hist_bin'].value_counts().sort_index()

# 히스토그램 그리기
plt.figure(figsize=(12, 6))
hist_counts.plot(kind='bar', color='skyblue', edgecolor='black')
plt.title("Squeeze Momentum Histogram (1000 Unit Section)")
plt.xlabel("Momentum Histogram Unit")
plt.ylabel("Frequency")
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

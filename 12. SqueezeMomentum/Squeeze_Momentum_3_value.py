import pandas as pd

# CSV 파일 불러오기
btc_df = pd.read_csv("./BTC_1d.csv")

# 열 이름 변경 (한국어 → 영문)
btc_df = btc_df.rename(columns={
    'Open_time': 'datetime',
    '시가': 'open',
    '고가': 'high',
    '저가': 'low',
    '종가': 'close',
    '거래량': 'volume'
})

# datetime 처리
btc_df['datetime'] = pd.to_datetime(btc_df['datetime'])
btc_df.set_index('datetime', inplace=True)

# 모멘텀 히스토그램 계산
momentum_period = 20
btc_df['momentum'] = btc_df['close'] - btc_df['close'].shift(momentum_period)
btc_df['mom_sma'] = btc_df['momentum'].rolling(momentum_period).mean()
btc_df['mom_hist'] = btc_df['momentum'] - btc_df['mom_sma']

# 1000 단위 구간 나누기
bins = list(range(-10000, 11000, 1000))  # -10000 ~ +10000 구간
labels = [f"{i} ~ {i+1000}" for i in bins[:-1]]
btc_df['hist_bin'] = pd.cut(btc_df['mom_hist'], bins=bins, labels=labels)

# -1000 ~ 1000 구간 제외한 후 빈도수 및 확률 재계산
exclude_range = ["-1000 ~ 0", "0 ~ 1000"]
filtered = btc_df[~btc_df['hist_bin'].isin(exclude_range)]

hist_counts = filtered['hist_bin'].value_counts().sort_index()
total_count = hist_counts.sum()
hist_percent = (hist_counts / total_count * 100).round(2)

# 결과 DataFrame 생성
result_df = pd.DataFrame({
    "횟수": hist_counts,
    "분포 확률(%)": hist_percent
})

# 출력
print(result_df)


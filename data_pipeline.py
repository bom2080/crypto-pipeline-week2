"""
금융 데이터 분석 파이프라인 — 2주차
======================================
노트북(01~04)의 전체 과정을 하나의 스크립트로 순서대로 실행합니다.

실행 방법:
    python data_pipeline.py

실행 결과:
    ohlcv_raw.csv          : 수집된 원본 데이터
    ohlcv_preprocessed.csv : price_change 지표 추가된 데이터
    ohlcv_final.csv        : ma5까지 추가된 최종 데이터
    close_ma5_chart.png    : 종가 + MA5 차트 이미지
"""

import pyupbit
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import warnings

warnings.filterwarnings('ignore')

# ── 설정 ──────────────────────────────────────────────────────────
TICKERS    = ["KRW-BTC", "KRW-ETH", "KRW-SOL"]
FETCH_DAYS = 60   # API에서 받아올 일수 (여유분 포함)
USE_DAYS   = 30   # 실제 분석에 사용할 최근 일수


# ── Step 1: 데이터 수집 ───────────────────────────────────────────
def collect_ohlcv(tickers, fetch_days, use_days):
    """여러 종목 OHLCV 데이터를 수집해 하나의 DataFrame으로 반환합니다."""
    all_frames = []

    for ticker in tickers:
        print(f"  [{ticker}] 수집 중...")
        try:
            df = pyupbit.get_ohlcv(ticker, count=fetch_days)
            if df is None or df.empty:
                continue

            df = df.tail(use_days).copy()
            df['date']   = pd.to_datetime(df.index.date)
            df['ticker'] = ticker
            df = df.reset_index(drop=True)
            all_frames.append(df)
            print(f"  [{ticker}] 완료 ({len(df)}일치)")

        except Exception as e:
            print(f"  [{ticker}] 오류: {e}, 건너뜀")
            continue

    # 여러 DataFrame을 세로로 합치기
    combined = pd.concat(all_frames, axis=0, ignore_index=True)

    # 필요한 컬럼만 선택하고 정렬
    cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
    combined = combined[cols].sort_values(['ticker', 'date']).reset_index(drop=True)
    return combined


# ── Step 2: 전처리 — 문제1 ────────────────────────────────────────
def add_price_features(df):
    """price_change, price_change_pct, high_low_diff 컬럼을 추가합니다."""
    df = df.copy()

    # 종가 - 시가 = 하루 동안의 가격 변동
    df['price_change'] = df['close'] - df['open']

    # 시가 대비 변동률 (%)
    df['price_change_pct'] = (df['price_change'] / df['open']) * 100

    # 고가 - 저가 = 하루 안에서의 최대 변동폭
    df['high_low_diff'] = df['high'] - df['low']

    return df


# ── Step 3: MA5 계산 — 문제2 ─────────────────────────────────────
def add_moving_average(df):
    """종목별 5일 이동평균(ma5)을 계산하고 NaN을 close 값으로 대체합니다."""
    df = df.copy()

    # groupby('ticker')로 종목별 분리 후 rolling(5).mean()으로 이동평균 계산
    # transform : 그룹별로 함수를 적용하되 원래 DataFrame 크기를 유지
    df['ma5'] = df.groupby('ticker')['close'].transform(
        lambda x: x.rolling(5).mean()
    )

    # 처음 4일은 데이터 부족으로 NaN → 해당 날의 종가(close)로 대체
    df['ma5'] = df['ma5'].fillna(df['close'])

    return df


# ── Step 4: 시각화 — 문제3 ───────────────────────────────────────
def plot_close_and_ma5(df, save_path='close_ma5_chart.png'):
    """종가와 MA5를 3종목 서브플롯으로 그리고 이미지로 저장합니다."""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    tickers = df['ticker'].unique()

    # 1행 × 종목 수 열의 서브플롯 생성
    fig, axes = plt.subplots(nrows=1, ncols=len(tickers), figsize=(18, 5))

    for i, ticker in enumerate(tickers):
        ax  = axes[i]
        tdf = df[df['ticker'] == ticker].sort_values('date')

        # 종가 → 검정 실선
        ax.plot(tdf['date'], tdf['close'],
                color='black', linewidth=1.5, label='종가(close)')

        # MA5 → 빨간 점선
        ax.plot(tdf['date'], tdf['ma5'],
                color='red', linewidth=1.2,
                linestyle='--', alpha=0.8, label='MA5 (5일 이동평균)')

        ax.set_title(ticker, fontsize=13, fontweight='bold')
        ax.set_xlabel('날짜', fontsize=10)
        if i == 0:
            ax.set_ylabel('가격 (원)', fontsize=10)

        # x축 날짜 포맷: '01-05' 형식
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=8)

        # y축 숫자에 쉼표 삽입 (89250000 → 89,250,000)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f'{x:,.0f}')
        )

        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle='--')

    fig.suptitle('암호화폐 종가 및 5일 이동평균선 (최근 30일)',
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()

    # 이미지 파일로 저장
    # bbox_inches='tight' : 그림 가장자리가 잘리지 않도록
    # dpi=150             : 해상도 (숫자 클수록 선명하지만 파일 크기 커짐)
    plt.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.show()
    print(f"차트 저장 완료 → {save_path}")


# ── 메인 실행 ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 40)
    print("금융 데이터 분석 파이프라인 시작")
    print("=" * 40)

    # Step 1: 데이터 수집
    print("\n[Step 1] 데이터 수집")
    df = collect_ohlcv(TICKERS, FETCH_DAYS, USE_DAYS)
    df.to_csv('ohlcv_raw.csv', index=False)
    print(f"  → ohlcv_raw.csv 저장 완료 ({len(df)}행)")

    # Step 2: 전처리 (문제1)
    print("\n[Step 2] 전처리 — price_change 계산")
    df = add_price_features(df)
    df.to_csv('ohlcv_preprocessed.csv', index=False)
    print("  → ohlcv_preprocessed.csv 저장 완료")

    # Step 3: MA5 계산 (문제2)
    print("\n[Step 3] MA5 계산 및 결측치 처리")
    df = add_moving_average(df)
    final_cols = [
        'ticker', 'date', 'open', 'high', 'low', 'close', 'volume',
        'price_change', 'price_change_pct', 'high_low_diff', 'ma5'
    ]
    df = df[final_cols]
    df.to_csv('ohlcv_final.csv', index=False)
    nan_count = df['ma5'].isnull().sum()
    print(f"  → ohlcv_final.csv 저장 완료 | NaN 개수: {nan_count}")

    # Step 4: 시각화 (문제3)
    print("\n[Step 4] 시각화")
    plot_close_and_ma5(df)

    print("\n파이프라인 완료!")

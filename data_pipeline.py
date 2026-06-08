"""
금융 데이터 분석 파이프라인 — 2주차
======================================
노트북(01~04)의 전체 과정을 하나의 스크립트로 실행합니다.

실행 방법:
    python data_pipeline.py

출력:
    ohlcv_raw.csv          : 수집된 원본 데이터
    ohlcv_preprocessed.csv : price_change 지표 추가
    ohlcv_final.csv        : ma5 추가 + 컬럼 정리 완료
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
FETCH_DAYS = 60   # API에서 받을 일수
USE_DAYS   = 30   # 실제 사용할 일수


# ── Step 1: 데이터 수집 ───────────────────────────────────────────
def collect_ohlcv(tickers, fetch_days, use_days):
    """여러 종목 OHLCV 데이터를 수집해 하나의 DataFrame으로 반환"""
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
            print(f"  [{ticker}] 오류: {e}")
            continue

    combined = pd.concat(all_frames, axis=0, ignore_index=True)
    cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
    combined = combined[cols].sort_values(['ticker', 'date']).reset_index(drop=True)
    return combined


# ── Step 2: 전처리 (문제1) ────────────────────────────────────────
def add_price_features(df):
    """price_change, price_change_pct, high_low_diff 컬럼 추가"""
    df = df.copy()
    df['price_change']     = df['close'] - df['open']
    df['price_change_pct'] = (df['price_change'] / df['open']) * 100
    df['high_low_diff']    = df['high'] - df['low']
    return df


# ── Step 3: MA5 계산 (문제2) ─────────────────────────────────────
def add_moving_average(df):
    """종목별 5일 이동평균(ma5) 계산 및 NaN → close 대체"""
    df = df.copy()
    df['ma5'] = df.groupby('ticker')['close'].transform(
        lambda x: x.rolling(5).mean()
    )
    df['ma5'] = df['ma5'].fillna(df['close'])
    return df


# ── Step 4: 시각화 (문제3) ───────────────────────────────────────
def plot_close_and_ma5(df, save_path='close_ma5_chart.png'):
    """종가 + MA5 서브플롯 차트 생성 및 저장"""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    tickers = df['ticker'].unique()

    fig, axes = plt.subplots(nrows=1, ncols=len(tickers), figsize=(18, 5))

    for i, ticker in enumerate(tickers):
        ax  = axes[i]
        tdf = df[df['ticker'] == ticker].sort_values('date')

        ax.plot(tdf['date'], tdf['close'],
                color='black', linewidth=1.5, label='종가(close)')
        ax.plot(tdf['date'], tdf['ma5'],
                color='red', linewidth=1.2,
                linestyle='--', alpha=0.8, label='MA5 (5일 이동평균)')

        ax.set_title(ticker, fontsize=13, fontweight='bold')
        ax.set_xlabel('날짜', fontsize=10)
        if i == 0:
            ax.set_ylabel('가격 (원)', fontsize=10)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=8)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f'{x:,.0f}')
        )
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle='--')

    fig.suptitle('암호화폐 종가 및 5일 이동평균선 (최근 30일)',
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.show()
    print(f"차트 저장 완료 → {save_path}")


# ── 메인 실행 ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 40)
    print("금융 데이터 분석 파이프라인 시작")
    print("=" * 40)

    # Step 1
    print("\n[Step 1] 데이터 수집")
    df = collect_ohlcv(TICKERS, FETCH_DAYS, USE_DAYS)
    df.to_csv('ohlcv_raw.csv', index=False)
    print(f"  → ohlcv_raw.csv 저장 ({len(df)}행)")

    # Step 2
    print("\n[Step 2] 전처리 (price_change 계산)")
    df = add_price_features(df)
    df.to_csv('ohlcv_preprocessed.csv', index=False)
    print("  → ohlcv_preprocessed.csv 저장")

    # Step 3
    print("\n[Step 3] MA5 계산")
    df = add_moving_average(df)
    final_cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume',
                  'price_change', 'price_change_pct', 'high_low_diff', 'ma5']
    df = df[final_cols]
    df.to_csv('ohlcv_final.csv', index=False)
    nan_count = df['ma5'].isnull().sum()
    print(f"  → ohlcv_final.csv 저장 | NaN 개수: {nan_count}")

    # Step 4
    print("\n[Step 4] 시각화")
    plot_close_and_ma5(df)

    print("\n파이프라인 완료!")

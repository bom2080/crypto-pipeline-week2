# Day 2 — 금융 데이터 분석 파이프라인

업비트 API로 암호화폐 시세 데이터를 수집하고,  
전처리 → 기술 지표 계산 → 시각화까지 연결하는 데이터 파이프라인을 구현했습니다.

---

## 파일 구성

| 파일 | 내용 |
|------|------|
| `01_data_collection.ipynb` | 업비트 API로 3종목 OHLCV 데이터 수집 |
| `02_preprocessing.ipynb` | [필수] 종가·시가 차이 계산 (`price_change`, `price_change_pct`, `high_low_diff`) |
| `03_moving_average.ipynb` | [필수] 5일 이동평균(MA5) 계산 및 결측치 처리 |
| `04_visualization.ipynb` | [도전] 종가 + MA5 라인 차트 시각화 |
| `data_pipeline.py` | 위 4단계를 하나의 스크립트로 실행 |

## 분석 종목

- KRW-BTC (비트코인)
- KRW-ETH (이더리움)
- KRW-SOL (솔라나)

## 실행 방법

```bash
pip install pyupbit pandas matplotlib

# 노트북은 01 → 02 → 03 → 04 순서로 실행
# 또는 스크립트 한 번에 실행
python data_pipeline.py
```

---

## 회고

### 배운 것

- `rolling().mean()`으로 이동평균을 계산하는 방법을 처음 알았다. 창문을 하루씩 밀면서 평균을 구한다는 개념이 이해하니까 꽤 직관적이었다.
- `groupby().transform()`을 써서 종목별로 나눠 계산하는 방법이 신기했다. 처음엔 그냥 `groupby().mean()`이랑 뭐가 다른지 몰랐는데, transform은 원래 DataFrame 크기를 그대로 유지해준다는 게 핵심이었다.
- NaN을 어떻게 처리할지 고민이 많았는데, 종가(close)로 대체하는 방식이 가장 자연스럽다는 걸 이해했다. 0으로 채우면 차트에서 가격이 0원으로 뚝 떨어지는 문제가 생긴다는 걸 직접 생각해보면서 납득됐다.
- `price_change_pct`(변동률 %)를 따로 계산하는 이유도 처음엔 몰랐는데, 가격대가 다른 종목끼리는 금액보다 비율로 비교해야 공정하다는 걸 알게 됐다.

### 어려웠던 점

- Long Format이 뭔지 처음엔 이해가 안 됐다. 종목마다 컬럼을 따로 만드는 게 자연스럽게 떠올랐는데, 행을 늘리는 방식이 왜 더 나은지 와닿는 데 시간이 좀 걸렸다.
- `groupby().transform()`에서 lambda를 쓰는 부분이 문법이 낯설어서 여러 번 읽어봤다.
- matplotlib x축 날짜 표시가 생각보다 까다로웠다. `mdates.DateFormatter`랑 `AutoDateLocator`를 같이 써야 한다는 걸 몰라서 처음엔 날짜가 다닥다닥 겹쳐서 나왔다.

### 다음에 해볼 것

- MA5 말고 MA20, MA60도 같이 그려서 단기·중기·장기 추세를 비교해보고 싶다.
- 계산한 데이터를 SQLite에 저장하고 SQL로 조회하는 것도 해볼 예정이다 (Day 3 내용).
- 변동률이 크게 튀는 날을 차트에서 표시하는 기능도 나중에 추가해보고 싶다.

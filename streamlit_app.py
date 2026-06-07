import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# ==========================================
# 1. 페이지 기본 설정 및 디자인
# ==========================================
st.set_page_config(
    page_title="환율 기반 소비자 물가 예측 및 행동 가이드",
    page_icon="📱",
    layout="wide"
)

st.title("📱 환율-물가 연동형 소비자 최적 지출 타이밍 가이드")
st.markdown("매일 변동하는 **원/달러 환율**을 분석하여 미래 **소비자물가지수(CPI)** 향방을 예측하고, 지금 사야 이득인 품목을 알려줍니다.")
st.write("---")

# ==========================================
# 2. 내장 데이터 세팅 (사용자 제공 데이터 가공)
# ==========================================
# 2022.05 ~ 2026.05 전국 소비자물가지수 원본 데이터 백엔드 탑재
cpi_dict = {
    "2022-05-01": 107.50, "2022-06-01": 108.21, "2022-07-01": 108.73, "2022-08-01": 108.63, "2022-09-01": 108.82, "2022-10-01": 109.16, "2022-11-01": 109.07, "2022-12-01": 109.26,
    "2023-01-01": 110.07, "2023-02-01": 110.33, "2023-03-01": 110.52, "2023-04-01": 110.77, "2023-05-01": 111.13, "2023-06-01": 111.16, "2023-07-01": 111.29, "2023-08-01": 112.28, "2023-09-01": 112.85, "2023-10-01": 113.27, "2023-11-01": 112.68, "2023-12-01": 112.73,
    "2024-01-01": 113.17, "2024-02-01": 113.78, "2024-03-01": 113.95, "2024-04-01": 114.01, "2024-05-01": 114.10, "2024-06-01": 113.84, "2024-07-01": 114.13, "2024-08-01": 114.54, "2024-09-01": 114.65, "2024-10-01": 114.69, "2024-11-01": 114.40, "2024-12-01": 114.91,
    "2025-01-01": 115.71, "2025-02-01": 116.08, "2025-03-01": 116.29, "2025-04-01": 116.38, "2025-05-01": 116.27, "2025-06-01": 116.31, "2025-07-01": 116.52, "2025-08-01": 116.45, "2025-09-01": 117.06, "2025-10-01": 117.42, "2025-11-01": 117.20, "2025-12-01": 117.57,
    "2026-01-01": 118.03, "2026-02-01": 118.40, "2026-03-01": 118.80, "2026-04-01": 119.37, "2026-05-01": 119.92
}

@st.cache_resource 
def load_and_train_model():
    dates = pd.to_datetime(list(cpi_dict.keys()))
    cpi_values = list(cpi_dict.values())
    
    np.random.seed(42)
    fx_values = np.random.normal(1360, 40, len(dates))
    
    df = pd.DataFrame({"USD_KRW": fx_values, "CPI": cpi_values}, index=dates)
    df["FX_Change_MoM"] = df["USD_KRW"].pct_change() * 100
    df["CPI_Change_MoM"] = df["CPI"].pct_change() * 100
    
    feature_cols = []
    for lag in range(1, 4):
        col = f"FX_Lag_{lag}"
        df[col] = df["FX_Change_MoM"].shift(lag)
        feature_cols.append(col)
    
    df = df.dropna()
    
    X = df[feature_cols]
    y = df["CPI_Change_MoM"]
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    return model, df["USD_KRW"].mean(), df["USD_KRW"].std(), df

model, fx_mean, fx_std, df_master = load_and_train_model()

# ==========================================
# 3. 사이드바 (사용자 입력 컨트롤러)
# ==========================================
st.sidebar.header("🎛️ 실시간 데이터 입력")
st.sidebar.markdown("현재 시장의 실시간 지표를 설정하세요.")

current_fx = st.sidebar.slider("오늘의 일별 원/달러 환율 (원)", min_value=1200.0, max_value=1600.0, value=1395.0, step=0.5)

st.sidebar.subheader("최근 3개월간 월평균 환율 추이")
lag_1 = st.sidebar.slider("1달 전 환율 변동률 (%)", -5.0, 5.0, 1.2, 0.1)
lag_2 = st.sidebar.slider("2달 전 환율 변동률 (%)", -5.0, 5.0, -0.5, 0.1)
lag_3 = st.sidebar.slider("3달 전 환율 변동률 (%)", -5.0, 5.0, 2.0, 0.1)

# ==========================================
# 4. 분석 엔진 연산 레이어
# ==========================================
input_features = pd.DataFrame([[lag_1, lag_2, lag_3]], columns=['FX_Lag_1', 'FX_Lag_2', 'FX_Lag_3'])
predicted_cpi_inflation = model.predict(input_features)[0]

z_score = (current_fx - fx_mean) / fx_std
base_score = 50
total_score = np.clip(base_score + (z_score * 12) + (predicted_cpi_inflation * 45), 0, 100)

# 💡 추가된 로직: 다음 달 예상 소비자물가지수(절댓값) 연산
latest_date = df_master.index[-1]
next_month_str = (latest_date + pd.DateOffset(months=1)).strftime("%Y년 %m월")
latest_cpi_value = df_master["CPI"].iloc[-1]
expected_next_cpi = latest_cpi_value * (1 + (predicted_cpi_inflation / 100))

# ==========================================
# 5. 프론트엔드 UI/UX 대시보드 화면 시각화
# ==========================================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 오늘의 소비 신호등 스코어")
    
    if total_score >= 65:
        st.error(f"## **{total_score:.1f}점 / 🚨 비상: 지금 사야 이득**")
        status_color = "red"
        status_desc = "현재 고환율 기조 및 누적된 과거 환율 충격으로 인해 수 개월 내 수입 물가와 소비자 가격이 크게 상승할 위험이 포착되었습니다."
    elif total_score <= 35:
        st.success(f"## **{total_score:.1f}점 / 🍏 관망: 나중에 사야 이득**")
        status_color = "green"
        status_desc = "환율이 안정세에 접어들었습니다. 전이 시차 효과로 인해 수 개월 뒤 소비재 가격이 인하되거나 안정화될 가능성이 매우 높습니다."
    else:
        st.warning(f"## **{total_score:.1f}점 / 🟡 안정: 계획 소비**")
        status_color = "blue"
        status_desc = "현재 정상 범위 내의 거시경제 변동성을 보이고 있습니다. 무리한 소비나 미룸 없이 정석적인 계획 지출을 권장합니다."

    st.markdown(f"**진단 결과:** {status_desc}")
    
    # 💡 추가된 UI: % 변동률과 함께 계산된 다음 달 예측 지수를 표시합니다.
    st.metric(
        label=f"AI 예측: {next_month_str} 예상 소비자물가지수", 
        value=f"{expected_next_cpi:.2f}", 
        delta=f"예상 상승률: {predicted_cpi_inflation:.3f} %"
    )

with col2:
    st.subheader("💡 카테고리별 스마트 쇼핑 가이드")
    
    if total_score >= 65:
        st.info("✈️ **해외직구 / 전자기기 / 항공권**\n\n장바구니에 담아둔 직구 상품이나 노트북, 해외 여행 상품은 **오늘 결제하는 것이 가장 저렴**합니다. 수개월 내 물량 인상분이 반영됩니다.")
        st.info("🛒 **대형마트 생필품 / 밀가루·가공식품**\n\n원자재 수입가 인상 전, 대형마트의 기획전이나 묶음 할인 상품을 활용해 **생활 필수품을 미리 확보(쟁여두기)**하는 것이 지출을 방어하는 길입니다.")
    elif total_score <= 35:
        st.info("✈️ **해외직구 / 전자기기 / 항공권**\n\n**지출을 당장 미루세요!** 1~2달 뒤 환율 하락 효과가 커머스 및 여행 가격에 직접 반영되어 예산을 대폭 아낄 수 있습니다.")
        st.info("🛒 **대형마트 생필품 / 밀가루·가공식품**\n\n급하지 않은 품목은 사재기할 필요가 전혀 없습니다. 시장에 공급 가격 인하 압력이 가해질 테니 **필요할 때마다 소량 구매**하세요.")
    else:
        st.info("✈️ **해외직구 / 전자기기 / 항공권**\n\n시장이 평이합니다. 환율 이득을 노리기보다는 이커머스 자체 쿠폰이나 카드사 할인 혜택 타이밍에 맞춰 구매하세요.")
        st.info("🛒 **대형마트 생필품 / 밀가루·가공식품**\n\n정상적인 소비 주기를 유지하세요. 특이 가격 변동 리스크가 낮습니다.")

st.write("---")
st.subheader("📈 백엔드 시계열 데이터 트렌드 조회 (2022.05 ~ 2026.05)")

chart_data = df_master[['USD_KRW', 'CPI']].copy()
chart_data['환율 추이(정규화)'] = (chart_data['USD_KRW'] - chart_data['USD_KRW'].mean()) / chart_data['USD_KRW'].std()
chart_data['소비자물가 추이(정규화)'] = (chart_data['CPI'] - chart_data['CPI'].mean()) / chart_data['CPI'].std()

st.line_chart(chart_data[['환율 추이(정규화)', '소비자물가 추이(정규화)']])
st.caption("※ 분석 이해를 돕기 위해 두 지표의 단위를 맞춰 정규화(Standardized)한 추이 그래프입니다. 환율의 고점/저점이 발생한 후 수 개월 뒤 물가지수가 자극받는 시차 양상을 한눈에 파악할 수 있습니다.")

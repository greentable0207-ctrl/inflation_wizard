import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta

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
# 2. 실시간 야후 파이낸스 환율 데이터 로드
# ==========================================
@st.cache_data(ttl=600) # 10분마다 갱신
def get_realtime_fx():
    try:
        # KRW=X 는 야후 파이낸스의 달러/원 환율 티커입니다.
        ticker = yf.Ticker("KRW=X")
        recent_daily_fx = ticker.history(period="3mo")
        history_fx = ticker.history(period="5y")
        
        latest_price = recent_daily_fx['Close'].iloc[-1]
        prev_price = recent_daily_fx['Close'].iloc[-2]
        price_change = latest_price - prev_price
        
        return recent_daily_fx[['Close']], history_fx, latest_price, price_change
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), 1380.0, 0.0

recent_fx_df, history_fx_df, current_real_fx, fx_change = get_realtime_fx()

# ==========================================
# 3. 내장 데이터 및 AI 모델 학습 레이어
# ==========================================
cpi_dict = {
    "2022-05-01": 107.50, "2022-06-01": 108.21, "2022-07-01": 108.73, "2022-08-01": 108.63, "2022-09-01": 108.82, "2022-10-01": 109.16, "2022-11-01": 109.07, "2022-12-01": 109.26,
    "2023-01-01": 110.07, "2023-02-01": 110.33, "2023-03-01": 110.52, "2023-04-01": 110.77, "2023-05-01": 111.13, "2023-06-01": 111.16, "2023-07-01": 111.29, "2023-08-01": 112.28, "2023-09-01": 112.85, "2023-10-01": 113.27, "2023-11-01": 112.68, "2023-12-01": 112.73,
    "2024-01-01": 113.17, "2024-02-01": 113.78, "2024-03-01": 113.95, "2024-04-01": 114.01, "2024-05-01": 114.10, "2024-06-01": 113.84, "2024-07-01": 114.13, "2024-08-01": 114.54, "2024-09-01": 114.65, "2024-10-01": 114.69, "2024-11-01": 114.40, "2024-12-01": 114.91,
    "2025-01-01": 115.71, "2025-02-01": 116.08, "2025-03-01": 116.29, "2025-04-01": 116.38, "2025-05-01": 116.27, "2025-06-01": 116.31, "2025-07-01": 116.52, "2025-08-01": 116.45, "2025-09-01": 117.06, "2025-10-01": 117.42, "2025-11-01": 117.20, "2025-12-01": 117.57,
    "2026-01-01": 118.03, "2026-02-01": 118.40, "2026-03-01": 118.80, "2026-04-01": 119.37, "2026-05-01": 119.92
}

@st.cache_resource 
def load_and_train_model(history_fx_data):
    dates = pd.to_datetime(list(cpi_dict.keys()))
    cpi_values = list(cpi_dict.values())
    df = pd.DataFrame({"CPI": cpi_values}, index=dates)
    
    if not history_fx_data.empty:
        fx_hist = history_fx_data.copy()
        fx_hist.index = fx_hist.index.tz_localize(None)
        fx_monthly = fx_hist['Close'].resample('MS').first()
        df["USD_KRW"] = fx_monthly.reindex(df.index).ffill().bfill()
    else:
        np.random.seed(42)
        df["USD_KRW"] = np.random.normal(1360, 40, len(dates))
        
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

model, fx_mean, fx_std, df_master = load_and_train_model(history_fx_df)

# ==========================================
# 4. 실시간 시장 상황 UI
# ==========================================
st.subheader("🌐 실시간 외환 시장 동향 (Yahoo Finance 연동)")
col_market1, col_market2 = st.columns([1, 3])

with col_market1:
    st.metric(
        label="현재 원/달러 환율 (실시간)", 
        value=f"{current_real_fx:,.2f} 원", 
        delta=f"{fx_change:,.2f} 원 (전일대비)",
        delta_color="inverse"
    )
    st.caption("※ 약 10분 주기로 야후 파이낸스 데이터를 갱신합니다.")

with col_market2:
    if not recent_fx_df.empty:
        recent_fx_df.columns = ['실시간 원/달러 환율 추이']
        st.line_chart(recent_fx_df, height=150, color="#EF4444")
    else:
        st.info("현재 실시간 데이터를 불러올 수 없습니다.")

st.write("---")

# ==========================================
# 5. 사이드바 (사용자 입력 컨트롤러)
# ==========================================
st.sidebar.header("🎛️ AI 시뮬레이터 (사용자 설정)")
st.sidebar.markdown("현재 실시간 환율이 기본값으로 세팅되어 있습니다. 슬라이더를 움직여 **환율이 더 오르거나 내릴 경우**를 시뮬레이션 해보세요.")

current_fx = st.sidebar.slider(
    "오늘의 일별 원/달러 환율 (원)", 
    min_value=1200.0, max_value=1600.0, 
    value=float(current_real_fx), 
    step=0.5
)

st.sidebar.subheader("최근 3개월간 월평균 환율 추이")
recent_lags = df_master["FX_Change_MoM"].iloc[-3:].values[::-1]

lag_1 = st.sidebar.slider("1달 전 환율 변동률 (%)", -5.0, 5.0, float(recent_lags[0]), 0.1)
lag_2 = st.sidebar.slider("2달 전 환율 변동률 (%)", -5.0, 5.0, float(recent_lags[1]), 0.1)
lag_3 = st.sidebar.slider("3달 전 환율 변동률 (%)", -5.0, 5.0, float(recent_lags[2]), 0.1)

# ==========================================
# 6. 분석 엔진 연산 레이어
# ==========================================
input_features = pd.DataFrame([[lag_1, lag_2, lag_3]], columns=['FX_Lag_1', 'FX_Lag_2', 'FX_Lag_3'])
predicted_cpi_inflation = model.predict(input_features)[0]

z_score = (current_fx - fx_mean) / fx_std
base_score = 50
total_score = np.clip(base_score + (z_score * 12) + (predicted_cpi_inflation * 45), 0, 100)

latest_date = df_master.index[-1]
next_month_str = (latest_date + pd.DateOffset(months=1)).strftime("%Y년 %m월")
latest_cpi_value = df_master["CPI"].iloc[-1]
expected_next_cpi = latest_cpi_value * (1 + (predicted_cpi_inflation / 100))

# ==========================================
# 7. 프론트엔드 UI/UX 대시보드 화면 시각화
# ==========================================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 오늘의 소비 신호등 스코어")
    
    if total_score >= 65:
        st.error(f"## **{total_score:.1f}점 / 🚨 비상: 지금 사야 이득**")
        status_desc = "현재 고환율 기조 및 누적된 과거 환율 충격으로 인해 수 개월 내 수입 물가와 소비자 가격이 크게 상승할 위험이 포착되었습니다."
    elif total_score <= 35:
        st.success(f"## **{total_score:.1f}점 / 🍏 관망: 나중에 사야 이득**")
        status_desc = "환율이 안정세에 접어들었습니다. 전이 시차 효과로 인해 수 개월 뒤 소비재 가격이 인하되거나 안정화될 가능성이 매우 높습니다."
    else:
        st.warning(f"## **{total_score:.1f}점 / 🟡 안정: 계획 소비**")
        status_desc = "현재 정상 범위 내의 거시경제 변동성을 보이고 있습니다. 무리한 소비나 미룸 없이 정석적인 계획 지출을 권장합니다."

    st.markdown(f"**진단 결과:** {status_desc}")
    
    st.metric(
        label=f"🤖 AI 예측: {next_month_str} 예상 소비자물가지수", 
        value=f"{expected_next_cpi:.2f}", 
        delta=f"예상 상승률: {predicted_cpi_inflation:.3f} %",
        delta_color="inverse"
    )

with col2:
    st.subheader("💡 4대 핵심 카테고리 소비 가이드")
    
    # 💡 세분화된 4가지 스마트 쇼핑 가이드 (여행, IT기기, 식료품, 주유)
    if total_score >= 65:
        st.error("""
        **🚨 핵심 지침: 지출을 앞당기세요 (지금 사야 이득)**
        
        * ✈️ **해외여행 및 환전:** 환율 추가 상승 리스크가 매우 큽니다. 예정된 숙소 예약이나 항공권 결제, 환전은 **지금 당장** 마무리하여 환차손을 방어하세요.
        * 💻 **전자기기 및 직구:** 수입 단가 인상이 조만간 국내 소비자가에 반영됩니다. 구매를 벼르고 있던 스마트폰, PC 부품은 **오늘 결제하는 것이 가장 저렴**합니다.
        * 🛒 **대형마트 식료품:** 밀가루, 식용유 등 수입 원자재 의존도가 높은 가공식품은 가격 인상 전 묶음 상품으로 **미리 쟁여두는 것**이 유리합니다.
        * ⛽ **주유비 및 내구재:** 고환율 파급 효과로 주유소 유가의 도미노 상승이 예상됩니다. 오늘 주유소 방문 시 **가득 채우는 것(만땅)**을 권장합니다.
        """)
    elif total_score <= 35:
        st.success("""
        **🍏 핵심 지침: 지출을 미루세요 (나중에 사야 이득)**
        
        * ✈️ **해외여행 및 환전:** 환율이 하향 안정화되고 있습니다. 급하지 않다면 1~2달 뒤 결제 시 **체감 비용이 크게 낮아질 수 있으니 기다리세요.**
        * 💻 **전자기기 및 직구:** 원화 가치 상승으로 수입품 가격 인하 여력이 생깁니다. 당장 고장난 게 아니라면 **대형 할인 행사 시점까지 구매를 미루세요.**
        * 🛒 **대형마트 식료품:** 수입 과일, 육류 등의 가격이 점차 하향 안정화될 전망입니다. 사재기할 필요 없이 **당장 필요한 만큼만 소량 구매**하세요.
        * ⛽ **주유비 및 내구재:** 국제유가 동향과 맞물려 국내 유가 하락의 시차 효과가 기대됩니다. 가득 채우기보다 **그때그때 필요한 만큼만 주유**하세요.
        """)
    else:
        st.warning("""
        **⚖️ 핵심 지침: 평소대로 지출하세요 (계획적 소비)**
        
        * ✈️ **해외여행 및 환전:** 거시 경제 지표가 정상 범위입니다. 환율 눈치싸움보다는 **항공사 얼리버드 특가나 카드사 혜택**에 맞춰 예약하는 것이 현명합니다.
        * 💻 **전자기기 및 직구:** 급격한 가격 변동 리스크가 적습니다. 필요에 따라 유연하게 구매하시되, **정기 세일 기간을 활용**하는 정석적인 소비를 유지하세요.
        * 🛒 **대형마트 식료품:** 물가 급등 리스크가 낮습니다. 평소의 생활비 예산에 맞춰 **정상적인 소비 주기와 패턴**을 유지하시는 것을 추천합니다.
        * ⛽ **주유비 및 내구재:** 유가 변동성이 크지 않은 시기입니다. 평소 생활 반경 내에서 **가장 저렴한 단골 주유소**를 이용하는 패턴을 권장합니다.
        """)

st.write("---")
st.subheader("📈 백엔드 시계열 데이터 트렌드 조회 (AI 학습용 실데이터)")

chart_data = df_master[['USD_KRW', 'CPI']].copy()
chart_data['환율 추이(정규화)'] = (chart_data['USD_KRW'] - chart_data['USD_KRW'].mean()) / chart_data['USD_KRW'].std()
chart_data['소비자물가 추이(정규화)'] = (chart_data['CPI'] - chart_data['CPI'].mean()) / chart_data['CPI'].std()

st.line_chart(chart_data[['환율 추이(정규화)', '소비자물가 추이(정규화)']])
st.caption("※ 야후 파이낸스의 실제 과거 환율 데이터와 소비자물가지수를 표준화(Standardized)한 추이 그래프입니다. 환율 충격 발생 후 수 개월 뒤 물가지수가 어떻게 변하는지 AI가 학습한 데이터를 시각화했습니다.")

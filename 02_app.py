import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Global Top 10 Stock Dashboard", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.main { background-color: #0a0a0f; }
[data-testid="stAppViewContainer"] { background-color: #0a0a0f; }
[data-testid="stSidebar"] { background-color: #111118; }
h1, h2, h3 { color: #ffffff; }
.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}
.metric-title { font-size: 0.7rem; letter-spacing: 0.15em; color: #888; text-transform: uppercase; margin-bottom: 0.4rem; }
.metric-value { font-size: 1.5rem; font-weight: 700; color: #fff; }
.metric-change-pos { font-size: 0.85rem; color: #00d4aa; margin-top: 0.2rem; }
.metric-change-neg { font-size: 0.85rem; color: #ff4d6d; margin-top: 0.2rem; }
.stMultiSelect > div { background: #1a1a2e; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

TOP10 = {
    "Apple":      "AAPL",
    "Microsoft":  "MSFT",
    "NVIDIA":     "NVDA",
    "Amazon":     "AMZN",
    "Alphabet":   "GOOGL",
    "Meta":       "META",
    "Tesla":      "TSLA",
    "Berkshire":  "BRK-B",
    "TSMC":       "TSM",
    "Samsung":    "005930.KS",
}

COLORS = ["#00d4aa","#4361ee","#f72585","#ffd60a","#7209b7","#4cc9f0","#ff6b35","#06ffa5","#c77dff","#ff9f1c"]

# ── Header ──
st.markdown("""
<div style='padding: 2rem 0 1rem; border-bottom: 1px solid #2a2a4a; margin-bottom: 2rem;'>
    <h1 style='font-size:2rem; font-weight:700; margin:0; color:#fff;'>
        📈 Global Top 10 <span style='color:#00d4aa;'>Stock Dashboard</span>
    </h1>
    <p style='color:#888; margin:0.4rem 0 0; font-size:0.85rem; letter-spacing:0.05em;'>
        시가총액 글로벌 TOP 10 · 최근 1년 주가 변화
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    selected = st.multiselect("종목 선택", list(TOP10.keys()), default=list(TOP10.keys()))
    period = st.selectbox("기간", ["1개월","3개월","6개월","1년"], index=3)
    chart_type = st.selectbox("차트 유형", ["수익률 비교 (정규화)","주가 추이","캔들스틱","상관관계 히트맵"])
    st.markdown("---")
    st.markdown("<div style='font-size:0.75rem;color:#555;'>데이터: Yahoo Finance<br>자동 갱신: 앱 새로고침 시</div>", unsafe_allow_html=True)

period_map = {"1개월": "1mo", "3개월": "3mo", "6개월": "6mo", "1년": "1y"}
yf_period  = period_map[period]

if not selected:
    st.warning("종목을 하나 이상 선택해주세요.")
    st.stop()

# ── Fetch data ──
@st.cache_data(ttl=3600)
def load_data(tickers, period):
    result = {}
    for name, ticker in tickers.items():
        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if not df.empty:
                result[name] = df
        except:
            pass
    return result

with st.spinner("📡 실시간 데이터 불러오는 중..."):
    selected_tickers = {k: TOP10[k] for k in selected}
    data = load_data(selected_tickers, yf_period)

if not data:
    st.error("데이터를 불러올 수 없어요. 잠시 후 다시 시도해주세요.")
    st.stop()

# ── Metric cards ──
cols = st.columns(len(data))
for i, (name, df) in enumerate(data.items()):
    try:
        close = df["Close"].squeeze()
        current = float(close.iloc[-1])
        start   = float(close.iloc[0])
        change  = (current - start) / start * 100
        with cols[i]:
            sign = "+" if change >= 0 else ""
            color_class = "metric-change-pos" if change >= 0 else "metric-change-neg"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{name}</div>
                <div class="metric-value">${current:,.0f}</div>
                <div class="{color_class}">{sign}{change:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
    except:
        pass

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ──
dark_layout = dict(
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#111118",
    font=dict(color="#ccc", family="Inter"),
    xaxis=dict(gridcolor="#1e1e2e", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1e1e2e", showgrid=True, zeroline=False),
    legend=dict(bgcolor="#1a1a2e", bordercolor="#2a2a4a", borderwidth=1),
    hovermode="x unified",
    margin=dict(l=20, r=20, t=50, b=20),
)

# 1. 수익률 비교 (정규화)
if chart_type == "수익률 비교 (정규화)":
    fig = go.Figure()
    for i, (name, df) in enumerate(data.items()):
        try:
            close = df["Close"].squeeze()
            norm  = (close / close.iloc[0] - 1) * 100
            fig.add_trace(go.Scatter(
                x=close.index, y=norm,
                name=name, line=dict(color=COLORS[i % len(COLORS)], width=2),
                hovertemplate=f"<b>{name}</b><br>%{{x|%Y-%m-%d}}<br>수익률: %{{y:.2f}}%<extra></extra>"
            ))
        except: pass
    fig.update_layout(**dark_layout, title=dict(text="📊 수익률 비교 (기간 시작 = 0%)", font=dict(color="#fff", size=16)))
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)

# 2. 주가 추이
elif chart_type == "주가 추이":
    fig = go.Figure()
    for i, (name, df) in enumerate(data.items()):
        try:
            close = df["Close"].squeeze()
            fig.add_trace(go.Scatter(
                x=close.index, y=close,
                name=name, line=dict(color=COLORS[i % len(COLORS)], width=2),
                hovertemplate=f"<b>{name}</b><br>%{{x|%Y-%m-%d}}<br>${{y:,.2f}}<extra></extra>"
            ))
        except: pass
    fig.update_layout(**dark_layout, title=dict(text="💹 주가 추이 (USD)", font=dict(color="#fff", size=16)))
    fig.update_yaxes(tickprefix="$")
    st.plotly_chart(fig, use_container_width=True)

# 3. 캔들스틱
elif chart_type == "캔들스틱":
    candle_name = st.selectbox("종목 선택", list(data.keys()))
    df = data[candle_name]
    try:
        fig = go.Figure(go.Candlestick(
            x=df.index,
            open=df["Open"].squeeze(),
            high=df["High"].squeeze(),
            low=df["Low"].squeeze(),
            close=df["Close"].squeeze(),
            increasing_line_color="#00d4aa",
            decreasing_line_color="#ff4d6d",
            name=candle_name,
        ))
        fig.update_layout(**dark_layout, title=dict(text=f"🕯️ {candle_name} 캔들스틱", font=dict(color="#fff", size=16)))
        fig.update_yaxes(tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"캔들 차트 오류: {e}")

# 4. 상관관계 히트맵
elif chart_type == "상관관계 히트맵":
    closes = {}
    for name, df in data.items():
        try:
            closes[name] = df["Close"].squeeze()
        except: pass
    if len(closes) >= 2:
        close_df = pd.DataFrame(closes).dropna()
        corr = close_df.corr()
        fig = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index,
            colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
            text=corr.round(2).values, texttemplate="%{text}",
            hovertemplate="%{x} vs %{y}<br>상관계수: %{z:.2f}<extra></extra>",
            colorbar=dict(tickfont=dict(color="#ccc")),
        ))
        fig.update_layout(**dark_layout, title=dict(text="🔥 주가 상관관계 히트맵", font=dict(color="#fff", size=16)))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<div style='font-size:0.75rem;color:#555;'>1.0 = 완전 양의 상관 / -1.0 = 완전 음의 상관</div>", unsafe_allow_html=True)
    else:
        st.warning("히트맵은 2개 이상 종목이 필요해요.")

# ── Volume bar ──
if chart_type in ["주가 추이", "수익률 비교 (정규화)"]:
    st.markdown("<br>", unsafe_allow_html=True)
    vol_name = st.selectbox("거래량 차트 종목", list(data.keys()), key="vol")
    try:
        vol_df = data[vol_name]
        vol    = vol_df["Volume"].squeeze()
        close  = vol_df["Close"].squeeze()
        colors = ["#00d4aa" if close.iloc[i] >= close.iloc[i-1] else "#ff4d6d" for i in range(len(close))]
        fig_vol = go.Figure(go.Bar(
            x=vol.index, y=vol, marker_color=colors, name="거래량",
            hovertemplate="%{x|%Y-%m-%d}<br>거래량: %{y:,.0f}<extra></extra>"
        ))
        fig_vol.update_layout(**dark_layout, height=250,
            title=dict(text=f"📊 {vol_name} 거래량", font=dict(color="#fff", size=14)))
        st.plotly_chart(fig_vol, use_container_width=True)
    except: pass

st.markdown("<div style='text-align:center;font-size:0.7rem;color:#333;padding:2rem 0;'>STOCK DASHBOARD · Data by Yahoo Finance · 투자 참고용, 투자 권유 아님</div>", unsafe_allow_html=True)

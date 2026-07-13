import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="서울시 공영주차장", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600&display=swap');
* { font-family: 'Noto Sans KR', sans-serif; }
[data-testid="stAppViewContainer"] { background: #f8f9fb; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e5e7eb; }
.page-title { font-size: 1.6rem; font-weight: 700; color: #111; margin-bottom: 0.2rem; }
.page-sub { font-size: 0.85rem; color: #6b7280; margin-bottom: 2rem; }
.stat-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.stat-label { font-size: 0.72rem; color: #9ca3af; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem; }
.stat-value { font-size: 1.8rem; font-weight: 700; color: #111; }
.stat-unit { font-size: 0.8rem; color: #6b7280; margin-left: 3px; }
.section-title { font-size: 0.75rem; font-weight: 600; color: #374151; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.5rem 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 1rem; }
div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# 컬럼명 후보 (서울 열린데이터광장 파일 버전마다 다름)
COL_CANDIDATES = {
    "자치구": ["자치구명", "자치구", "구명", "시군구명"],
    "주차장명": ["주차장명", "주차장 명", "명칭"],
    "주차장구분": ["주차장구분", "주차장구분명", "구분", "종류"],
    "위도": ["위도", "lat", "latitude", "y좌표", "y_coord"],
    "경도": ["경도", "lng", "longitude", "x좌표", "x_coord"],
    "주소": ["소재지도로명주소", "소재지지번주소", "주소", "도로명주소"],
    "주차구획수": ["주차구획수", "구획수", "면수"],
    "요금구분": ["요금정보구분명", "요금구분", "유무료구분", "요금유형"],
}

TYPE_COLORS = {
    "노외": "#2563eb",
    "노상": "#16a34a",
    "부설": "#d97706",
    "기타": "#6b7280",
}

GU_LIST = [
    "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구",
    "노원구","도봉구","동대문구","동작구","마포구","서대문구","서초구","성동구",
    "성북구","송파구","양천구","영등포구","용산구","은평구","종로구","중구","중랑구"
]

def find_col(df, key):
    for c in COL_CANDIDATES[key]:
        if c in df.columns:
            return c
        for col in df.columns:
            if c in col or col in c:
                return col
    return None

def normalize_type(val):
    if pd.isna(val): return "기타"
    val = str(val).strip()
    for t in ["노외", "노상", "부설"]:
        if t in val: return t
    return "기타"

# ── Header ──
st.markdown('<div class="page-title">서울시 공영주차장</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">서울 열린데이터광장 CSV 업로드 후 자치구 · 주차장 종류별로 지도에서 확인합니다.</div>', unsafe_allow_html=True)

# ── 파일 업로드 ──
uploaded = st.file_uploader("CSV 파일 업로드", type=["csv"], label_visibility="collapsed")

if uploaded is None:
    st.info("서울 열린데이터광장(data.seoul.go.kr)에서 '서울시 공영주차장' CSV를 내려받아 업로드하세요.")
    st.markdown("""
    **필요한 파일**  
    서울 열린데이터광장 → 검색: `서울시 공영주차장 안내 정보` → CSV 다운로드

    **필수 포함 컬럼**  
    자치구명, 주차장명, 주차장구분, 위도, 경도
    """)
    st.stop()

# ── 데이터 로드 ──
try:
    try:
        df_raw = pd.read_csv(uploaded, encoding="utf-8")
    except UnicodeDecodeError:
        uploaded.seek(0)
        df_raw = pd.read_csv(uploaded, encoding="cp949")
except Exception as e:
    st.error(f"파일을 읽을 수 없습니다: {e}")
    st.stop()

# ── 컬럼 매핑 ──
col_map = {key: find_col(df_raw, key) for key in COL_CANDIDATES}
missing = [k for k, v in col_map.items() if v is None and k in ["자치구", "주차장명", "위도", "경도"]]
if missing:
    st.error(f"필수 컬럼을 찾을 수 없습니다: {missing}\n\n전체 컬럼: {list(df_raw.columns)}")
    st.stop()

df = df_raw.copy()
df["_자치구"]    = df[col_map["자치구"]].astype(str).str.strip() if col_map["자치구"] else "알수없음"
df["_주차장명"]  = df[col_map["주차장명"]].astype(str).str.strip() if col_map["주차장명"] else "-"
df["_구분"]      = df[col_map["주차장구분"]].apply(normalize_type) if col_map["주차장구분"] else "기타"
df["_주소"]      = df[col_map["주소"]].astype(str).str.strip() if col_map["주소"] else "-"
df["_구획수"]    = pd.to_numeric(df[col_map["주차구획수"]], errors="coerce") if col_map["주차구획수"] else None
df["_요금"]      = df[col_map["요금구분"]].astype(str).str.strip() if col_map["요금구분"] else "-"

try:
    df["_위도"] = pd.to_numeric(df[col_map["위도"]], errors="coerce")
    df["_경도"] = pd.to_numeric(df[col_map["경도"]], errors="coerce")
except:
    st.error("위도/경도 컬럼 변환 실패")
    st.stop()

df = df.dropna(subset=["_위도", "_경도"])
df = df[(df["_위도"] > 37.4) & (df["_위도"] < 37.7) & (df["_경도"] > 126.7) & (df["_경도"] < 127.3)]

# ── 사이드바 필터 ──
with st.sidebar:
    st.markdown('<div class="section-title">필터</div>', unsafe_allow_html=True)

    type_options = sorted(df["_구분"].unique().tolist())
    selected_type = st.multiselect(
        "주차장 종류",
        options=type_options,
        default=type_options,
        placeholder="종류 선택"
    )

    st.markdown("---")
    st.markdown('<div class="section-title">주차장 종류 안내</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.8rem;color:#374151;line-height:2">
    <b>노외</b> — 도로 밖 주차장 (공영 주차빌딩 등)<br>
    <b>노상</b> — 도로 위 주차 구역<br>
    <b>부설</b> — 건물 부속 주차장
    </div>
    """, unsafe_allow_html=True)
# ── 필터 적용 ──
filtered = df.copy()
if selected_gu:
    filtered = filtered[filtered["_자치구"].isin(selected_gu)]
if selected_type:
    filtered = filtered[filtered["_구분"].isin(selected_type)]

if filtered.empty:
    st.warning("선택한 조건에 해당하는 주차장이 없습니다.")
    st.stop()

# ── 통계 카드 ──
c1, c2, c3, c4 = st.columns(4)
cards = [
    ("전체 주차장", f"{len(filtered):,}", "개소"),
    ("총 주차 면수", f"{int(filtered['_구획수'].sum()):,}" if col_map["주차구획수"] else "-", "면"),
    ("자치구", f"{filtered['_자치구'].nunique()}", "개"),
    ("주차장 종류", f"{filtered['_구분'].nunique()}", "종"),
]
for col, (label, val, unit) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{val}<span class="stat-unit">{unit}</span></div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── 지도 ──
st.markdown('<div class="section-title">위치 지도</div>', unsafe_allow_html=True)

filtered["_색상"] = filtered["_구분"].map(TYPE_COLORS).fillna("#6b7280")

hover_cols = ["_주차장명", "_자치구", "_구분", "_주소"]
if col_map["주차구획수"]: hover_cols.append("_구획수")
if col_map["요금구분"]:   hover_cols.append("_요금")

hover_labels = {
    "_주차장명": "주차장명",
    "_자치구": "자치구",
    "_구분": "종류",
    "_주소": "주소",
    "_구획수": "주차면수",
    "_요금": "요금구분",
}

fig_map = px.scatter_mapbox(
    filtered,
    lat="_위도", lon="_경도",
    color="_구분",
    color_discrete_map=TYPE_COLORS,
    hover_name="_주차장명",
    hover_data={k: True for k in hover_cols if k in filtered.columns and k != "_주차장명"},
    labels=hover_labels,
    zoom=11,
    center={"lat": filtered["_위도"].mean(), "lon": filtered["_경도"].mean()},
    height=560,
)
fig_map.update_traces(marker=dict(size=7, opacity=0.8))
fig_map.update_layout(
    mapbox_style="carto-positron",
    paper_bgcolor="#f8f9fb",
    plot_bgcolor="#f8f9fb",
    margin=dict(l=0, r=0, t=0, b=0),
    legend=dict(
        title="주차장 종류",
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#e5e7eb",
        borderwidth=1,
        font=dict(size=12),
    ),
)
st.plotly_chart(fig_map, use_container_width=True)

# ── 자치구별 현황 ──
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-title">자치구별 주차장 수</div>', unsafe_allow_html=True)
    gu_count = filtered.groupby("_자치구").size().reset_index(name="주차장수").sort_values("주차장수", ascending=True)
    fig_bar = px.bar(
        gu_count, x="주차장수", y="_자치구",
        orientation="h",
        color="주차장수",
        color_continuous_scale=["#bfdbfe", "#2563eb"],
        labels={"_자치구": "", "주차장수": "주차장 수"},
        height=420,
    )
    fig_bar.update_layout(
        paper_bgcolor="#f8f9fb", plot_bgcolor="#f8f9fb",
        coloraxis_showscale=False,
        margin=dict(l=0, r=20, t=10, b=10),
        xaxis=dict(gridcolor="#e5e7eb"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        font=dict(family="Noto Sans KR", size=12),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.markdown('<div class="section-title">주차장 종류 비율</div>', unsafe_allow_html=True)
    type_count = filtered["_구분"].value_counts().reset_index()
    type_count.columns = ["종류", "수"]
    fig_pie = px.pie(
        type_count, names="종류", values="수",
        color="종류",
        color_discrete_map=TYPE_COLORS,
        hole=0.45,
        height=420,
    )
    fig_pie.update_traces(textposition="outside", textinfo="label+percent", textfont_size=12)
    fig_pie.update_layout(
        paper_bgcolor="#f8f9fb",
        margin=dict(l=20, r=20, t=30, b=10),
        showlegend=False,
        font=dict(family="Noto Sans KR"),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── 데이터 테이블 ──
st.markdown('<div class="section-title">주차장 목록</div>', unsafe_allow_html=True)

display_cols = {"_주차장명": "주차장명", "_자치구": "자치구", "_구분": "종류", "_주소": "주소"}
if col_map["주차구획수"]: display_cols["_구획수"] = "주차면수"
if col_map["요금구분"]:   display_cols["_요금"] = "요금구분"

table = filtered[list(display_cols.keys())].rename(columns=display_cols).reset_index(drop=True)
table.index += 1
st.dataframe(table, use_container_width=True, height=360)

st.markdown("<div style='text-align:center;font-size:0.7rem;color:#d1d5db;padding:2rem 0 0.5rem;'>데이터 출처: 서울 열린데이터광장 · 지도: OpenStreetMap</div>", unsafe_allow_html=True)

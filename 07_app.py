import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="관광지 추천맵", page_icon="🗺️", layout="wide")

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"

AREA_CODES = {
    "서울": "1", "인천": "2", "대전": "3", "대구": "4", "광주": "5",
    "부산": "6", "울산": "7", "세종": "8", "경기": "31", "강원": "32",
    "충북": "33", "충남": "34", "경북": "35", "경남": "36", "전북": "37",
    "전남": "38", "제주": "39",
}

CONTENT_TYPES = {
    "관광지": "12", "문화시설": "14", "축제/공연/행사": "15",
    "여행코스": "25", "레포츠": "28", "숙박": "32", "쇼핑": "38", "음식점": "39",
}

MARKER_COLORS = {
    "관광지": "green", "문화시설": "purple", "축제/공연/행사": "red",
    "여행코스": "orange", "레포츠": "blue", "숙박": "darkblue",
    "쇼핑": "pink", "음식점": "cadetblue",
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_sigungu(service_key: str, area_code: str) -> dict:
    """선택한 시/도의 시/군/구 목록을 {이름: 코드} 형태로 반환"""
    params = {
        "serviceKey": service_key,
        "MobileOS": "ETC",
        "MobileApp": "TourRecommendApp",
        "_type": "json",
        "areaCode": area_code,
        "numOfRows": 100,
    }
    r = requests.get(f"{BASE_URL}/areaCode2", params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    items = data["response"]["body"]["items"]
    if items == "":
        return {}
    item_list = items["item"]
    if isinstance(item_list, dict):
        item_list = [item_list]
    return {i["name"]: i["code"] for i in item_list}


@st.cache_data(ttl=1800, show_spinner=False)
def get_places(service_key: str, area_code: str, sigungu_code: str | None,
                content_type_id: str | None, num_rows: int = 100) -> pd.DataFrame:
    """지역기반 관광정보 목록 조회"""
    params = {
        "serviceKey": service_key,
        "MobileOS": "ETC",
        "MobileApp": "TourRecommendApp",
        "_type": "json",
        "arrangeType": "A",
        "areaCode": area_code,
        "numOfRows": num_rows,
        "pageNo": 1,
    }
    if sigungu_code:
        params["sigunguCode"] = sigungu_code
    if content_type_id:
        params["contentTypeId"] = content_type_id

    r = requests.get(f"{BASE_URL}/areaBasedList2", params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    body = data["response"]["body"]
    if int(body["totalCount"]) == 0:
        return pd.DataFrame()
    item_list = body["items"]["item"]
    if isinstance(item_list, dict):
        item_list = [item_list]
    return pd.DataFrame(item_list)


# ---------- Sidebar ----------
st.sidebar.header("⚙️ 설정")

default_key = ""
try:
    default_key = st.secrets.get("TOUR_API_KEY", "")
except Exception:
    pass

service_key = st.sidebar.text_input(
    "공공데이터포털 서비스키 (Decoding)",
    value=default_key,
    type="password",
    help="data.go.kr > '한국관광공사_국문 관광정보 서비스_GW' 활용신청 후 발급받은 일반 인증키(Decoding)를 입력하세요.",
)

area_name = st.sidebar.selectbox("시/도", list(AREA_CODES.keys()))
area_code = AREA_CODES[area_name]

sigungu_map: dict = {}
if service_key:
    try:
        sigungu_map = get_sigungu(service_key, area_code)
    except Exception as e:
        st.sidebar.error(f"시/군/구 조회 실패: {e}")

sigungu_name = st.sidebar.selectbox("시/군/구", ["전체"] + list(sigungu_map.keys()))
sigungu_code = sigungu_map.get(sigungu_name)

content_names = st.sidebar.multiselect(
    "관광 타입", list(CONTENT_TYPES.keys()), default=["관광지"]
)

search_btn = st.sidebar.button("🔍 검색", type="primary", use_container_width=True)

# ---------- Main ----------
st.title("🗺️ 지역·테마별 관광지 추천")
st.caption("한국관광공사 TourAPI(관광정보서비스) 기반")

if not service_key:
    st.info(
        "사이드바에 공공데이터포털 서비스키를 입력하세요.\n\n"
        "1. data.go.kr 접속 → 회원가입/로그인\n"
        "2. '한국관광공사_국문 관광정보 서비스_GW' 검색 후 활용신청\n"
        "3. 마이페이지 > 개발계정에서 **일반 인증키(Decoding)** 복사"
    )
    st.stop()

if search_btn:
    if not content_names:
        st.warning("관광 타입을 하나 이상 선택하세요.")
    else:
        frames = []
        with st.spinner("관광정보를 불러오는 중..."):
            for name in content_names:
                ct_id = CONTENT_TYPES[name]
                try:
                    df = get_places(service_key, area_code, sigungu_code, ct_id)
                except Exception as e:
                    st.error(f"'{name}' 조회 실패: {e}")
                    continue
                if not df.empty:
                    df["타입"] = name
                    frames.append(df)
        st.session_state["result_df"] = (
            pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        )

result = st.session_state.get("result_df", pd.DataFrame())

if result.empty:
    if "result_df" in st.session_state:
        st.warning("검색 결과가 없습니다. 다른 지역이나 타입을 선택해보세요.")
else:
    # 좌표 없는 행 제거
    result = result[(result["mapx"].astype(str) != "") & (result["mapy"].astype(str) != "")]
    st.success(f"총 **{len(result)}건**의 관광정보를 찾았습니다.")

    col_map, col_list = st.columns([2, 1])

    with col_map:
        center_lat = result["mapy"].astype(float).mean()
        center_lng = result["mapx"].astype(float).mean()
        m = folium.Map(location=[center_lat, center_lng], zoom_start=12, tiles="CartoDB positron")

        for _, row in result.iterrows():
            try:
                lat, lng = float(row["mapy"]), float(row["mapx"])
            except (ValueError, TypeError):
                continue
            popup_html = (
                f"<b>{row.get('title', '')}</b><br>"
                f"{row.get('addr1', '')}"
            )
            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=row.get("title", ""),
                icon=folium.Icon(color=MARKER_COLORS.get(row.get("타입"), "gray"), icon="info-sign"),
            ).add_to(m)

        st_folium(m, width=None, height=620, key="tour_map")

    with col_list:
        st.subheader("📋 목록")
        for _, row in result.sort_values("title").iterrows():
            with st.container(border=True):
                st.markdown(f"**{row.get('title', '(제목 없음)')}**")
                st.caption(f"{row.get('타입', '')} · {row.get('addr1', '주소 정보 없음')}")
                img = row.get("firstimage")
                if isinstance(img, str) and img:
                    st.image(img, use_container_width=True)

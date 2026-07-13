import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="WEATHERFIT", page_icon="🌤️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #F7F6F3; color: #1A1A1A; }
.wf-logo { font-family: 'DM Serif Display', serif; font-size: 2.8rem; letter-spacing: 0.15em; text-align:center; margin:0; }
.wf-sub { font-size: 0.8rem; letter-spacing: 0.25em; color: #888; text-align:center; text-transform:uppercase; margin-bottom:2rem; }
.weather-card { background:#1A1A1A; color:#F7F6F3; border-radius:20px; padding:2rem; text-align:center; }
.weather-temp { font-family:'DM Serif Display',serif; font-size:4rem; line-height:1; margin:0.5rem 0; }
.weather-meta { display:flex; justify-content:space-around; margin-top:1.5rem; padding-top:1.5rem; border-top:1px solid #333; font-size:0.8rem; color:#aaa; }
.weather-meta b { color:#F7F6F3; font-size:1rem; display:block; }
.section-label { font-size:0.7rem; letter-spacing:0.25em; text-transform:uppercase; color:#888; margin-bottom:1rem; padding-bottom:0.5rem; border-bottom:1px solid #E0DED8; }
.outfit-tag { display:inline-block; background:#1A1A1A; color:#F7F6F3; font-size:0.7rem; padding:4px 10px; border-radius:20px; margin:3px 3px 0 0; }
.music-card { background:white; border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.8rem; border:1px solid #E0DED8; text-decoration:none; color:inherit; display:flex; align-items:center; gap:1rem; }
.music-idx { font-family:'DM Serif Display',serif; font-size:1.4rem; color:#ddd; min-width:24px; }
.stButton > button { border-radius:30px; background:#1A1A1A; color:white; border:none; padding:0.6rem 2rem; width:100%; }
.stTextInput > div > div > input { border-radius:30px; border:1.5px solid #E0DED8; padding:0.6rem 1.2rem; }
</style>
""", unsafe_allow_html=True)

OUTFIT_DB = {
    "freezing": {
        "label": "FREEZING — 체감 혹한",
        "items": ["두꺼운 패딩", "기모 레이어링", "목도리 + 장갑", "방한 부츠", "핫팩 필수"],
        "tags": ["heavy coat", "thermal layer", "scarf", "gloves", "winter boots"],
        "style_note": "레이어링이 핵심. 발열내의부터 시작해 아우터까지 단계별로.",
        "color_tip": "🎨 네이비·카키·버건디",
    },
    "cold": {
        "label": "COLD — 코트 필수",
        "items": ["울 코트 or 숏패딩", "니트 스웨터", "두꺼운 데님", "앵클부츠", "비니 or 머플러"],
        "tags": ["wool coat", "knit sweater", "thick denim", "ankle boots", "beanie"],
        "style_note": "코트 하나로 전체 룩의 격이 달라짐. 이너는 심플하게.",
        "color_tip": "🎨 카멜·오트밀·딥그린",
    },
    "cool": {
        "label": "COOL — 가디건 레이어",
        "items": ["트렌치코트", "가디건 레이어링", "슬랙스 or 긴 스커트", "로퍼 or 첼시부츠", "라이트 스카프"],
        "tags": ["trench coat", "cardigan", "slacks", "loafers", "light scarf"],
        "style_note": "트렌치코트 하나면 봄·가을 다 커버.",
        "color_tip": "🎨 베이지·그레이·버터옐로",
    },
    "mild": {
        "label": "MILD — 딱 좋은 날씨",
        "items": ["린넨 셔츠 or 블라우스", "와이드 팬츠 or 미디 스커트", "스니커즈 or 뮬", "가벼운 재킷 (저녁용)"],
        "tags": ["linen shirt", "wide pants", "midi skirt", "sneakers", "light jacket"],
        "style_note": "이 온도가 룩을 가장 예쁘게 소화할 수 있는 황금 구간.",
        "color_tip": "🎨 민트·라벤더·크림",
    },
    "warm": {
        "label": "WARM — 여름 진입",
        "items": ["반소매 티 or 크롭탑", "데님 쇼츠 or 플로럴 드레스", "샌들 or 에스파드리유", "선글라스", "미니 크로스백"],
        "tags": ["crop top", "denim shorts", "sundress", "sandals", "sunglasses"],
        "style_note": "패턴과 컬러로 승부. 액세서리 하나로 룩 완성도를 올려.",
        "color_tip": "🎨 코랄·화이트·터쿼이즈",
    },
    "hot": {
        "label": "HOT — 시원함이 최우선",
        "items": ["린넨 or 쿨링 소재 원피스", "반바지 + 루즈핏 탑", "슬리퍼 or 조리", "버킷햇 or 밀짚모자", "선크림 필수"],
        "tags": ["linen dress", "loose top", "shorts", "bucket hat", "slides"],
        "style_note": "소재가 전부. 린넨·모달 소재로 통기성 확보.",
        "color_tip": "🎨 오프화이트·세이지·스카이블루",
    },
}

MUSIC_DB = {
    "freezing": [
        {"title": "Snowfall", "artist": "Øneheart", "query": "Øneheart Snowfall"},
        {"title": "Winter", "artist": "Vivaldi", "query": "Vivaldi Winter Four Seasons"},
        {"title": "Blinding Lights", "artist": "The Weeknd", "query": "The Weeknd Blinding Lights"},
    ],
    "cold": [
        {"title": "willow", "artist": "Taylor Swift", "query": "Taylor Swift willow"},
        {"title": "Skinny Love", "artist": "Bon Iver", "query": "Bon Iver Skinny Love"},
        {"title": "505", "artist": "Arctic Monkeys", "query": "Arctic Monkeys 505"},
    ],
    "cool": [
        {"title": "Autumn Leaves", "artist": "Nat King Cole", "query": "Nat King Cole Autumn Leaves"},
        {"title": "Vienna", "artist": "Billy Joel", "query": "Billy Joel Vienna"},
        {"title": "505", "artist": "Arctic Monkeys", "query": "Arctic Monkeys 505"},
    ],
    "mild": [
        {"title": "Here Comes the Sun", "artist": "The Beatles", "query": "Beatles Here Comes The Sun"},
        {"title": "Good Days", "artist": "SZA", "query": "SZA Good Days"},
        {"title": "Peach", "artist": "IU (아이유)", "query": "IU 아이유 Peach"},
    ],
    "warm": [
        {"title": "Levitating", "artist": "Dua Lipa", "query": "Dua Lipa Levitating"},
        {"title": "As It Was", "artist": "Harry Styles", "query": "Harry Styles As It Was"},
        {"title": "SUMMER", "artist": "Calvin Harris", "query": "Calvin Harris Summer"},
    ],
    "hot": [
        {"title": "Watermelon Sugar", "artist": "Harry Styles", "query": "Harry Styles Watermelon Sugar"},
        {"title": "Sunflower", "artist": "Post Malone", "query": "Post Malone Sunflower"},
        {"title": "Levitating", "artist": "Dua Lipa", "query": "Dua Lipa Levitating"},
    ],
}

IMAGES_DB = {
    "freezing": ["https://images.unsplash.com/photo-1548883354-94bcfe321cbb?w=400&h=500&fit=crop", "https://images.unsplash.com/photo-1511401139252-f158d3209c17?w=400&h=500&fit=crop"],
    "cold":     ["https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=400&h=500&fit=crop", "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=500&fit=crop"],
    "cool":     ["https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop", "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&h=500&fit=crop"],
    "mild":     ["https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400&h=500&fit=crop", "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=400&h=500&fit=crop"],
    "warm":     ["https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=500&fit=crop", "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400&h=500&fit=crop"],
    "hot":      ["https://images.unsplash.com/photo-1504198266287-1659872e6590?w=400&h=500&fit=crop", "https://images.unsplash.com/photo-1485462537746-965f33f7f6a7?w=400&h=500&fit=crop"],
}

def get_category(temp):
    if temp < 0:   return "freezing"
    if temp < 10:  return "cold"
    if temp < 17:  return "cool"
    if temp < 23:  return "mild"
    if temp < 28:  return "warm"
    return "hot"

def get_icon(main):
    return {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️","Drizzle":"🌦️","Snow":"❄️","Thunderstorm":"⛈️","Mist":"🌫️","Fog":"🌫️"}.get(main,"🌤️")

def fetch_weather(city, api_key):
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric", "lang": "kr"}, timeout=8)
        if r.status_code == 401: return None, "API 키가 유효하지 않아요."
        if r.status_code == 404: return None, f"'{city}' 도시를 찾을 수 없어요."
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

# ── Header ──
st.markdown('<p class="wf-logo">WEATHERFIT</p>', unsafe_allow_html=True)
st.markdown('<p class="wf-sub">날씨에 맞는 오늘의 룩 · Weather-based outfit curator</p>', unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    api_key = st.text_input("OpenWeatherMap API Key", type="password", placeholder="API 키 입력")
    st.markdown("[🔑 무료 API 키 발급](https://openweathermap.org/api)", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""**앱 기능**  
🌤️ 실시간 날씨 정보  
👗 온도별 스타일 추천  
📸 패션 이미지 큐레이션  
🎵 날씨 무드 플레이리스트  
🎨 컬러 팔레트 제안""")

# ── Search ──
c1, c2 = st.columns([4, 1])
with c1:
    city = st.text_input("", placeholder="도시 이름 입력 (예: Seoul, Tokyo, Paris)", label_visibility="collapsed")
with c2:
    search = st.button("날씨 확인")

# ── Default: feature intro ──
if not search or not city:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">이렇게 사용해요</p>', unsafe_allow_html=True)
    for icon, title, desc in [
        ("🌤️","실시간 날씨","전 세계 도시의 온도·습도·날씨를 바로 확인"),
        ("👗","스타일 추천","6단계 온도 구간별 최적 코디 아이템 큐레이션"),
        ("📸","패션 이미지","추천 룩을 실제 이미지로 직관적으로 확인"),
        ("🎵","무드 플레이리스트","날씨 분위기에 맞는 YouTube 음악 바로가기"),
    ]:
        st.markdown(f"**{icon} {title}** — {desc}")
    st.info("👆 사이드바에 API 키를 입력하고, 도시 이름을 검색해보세요!")
    st.stop()

if not api_key:
    st.warning("⚠️ 사이드바에서 API 키를 먼저 입력해주세요.")
    st.stop()

# ── Fetch ──
with st.spinner("날씨 불러오는 중..."):
    data, err = fetch_weather(city, api_key)
if err:
    st.error(f"❌ {err}")
    st.stop()

# ── Parse ──
temp       = data["main"]["temp"]
feels_like = data["main"]["feels_like"]
humidity   = data["main"]["humidity"]
wind       = data["wind"]["speed"]
desc       = data["weather"][0]["description"]
w_main     = data["weather"][0]["main"]
city_name  = data["name"]
country    = data["sys"]["country"]
cat        = get_category(temp)
outfit     = OUTFIT_DB[cat]
music      = MUSIC_DB[cat]
images     = IMAGES_DB[cat]

# ── Layout ──
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown(f"""
    <div class="weather-card">
        <div style="font-size:0.75rem;letter-spacing:0.2em;color:#aaa;text-transform:uppercase">{city_name}, {country}</div>
        <div style="font-size:3rem;margin:0.3rem 0">{get_icon(w_main)}</div>
        <div class="weather-temp">{temp:.0f}°C</div>
        <div style="color:#ccc;margin-top:0.3rem">{desc}</div>
        <div class="weather-meta">
            <span><b>{feels_like:.0f}°</b>체감</span>
            <span><b>{humidity}%</b>습도</span>
            <span><b>{wind}m/s</b>바람</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<p class="section-label">TODAY\'S STYLE — {outfit["label"]}</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:white;border-radius:12px;padding:1.2rem 1.5rem;border:1px solid #E0DED8;">
        <div style="font-size:0.8rem;color:#444;line-height:1.9">
            {"<br>".join(f"· {i}" for i in outfit["items"])}
        </div>
        <div style="margin-top:0.8rem">
            {"".join(f'<span class="outfit-tag">{t}</span>' for t in outfit["tags"])}
        </div>
        <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid #f0f0f0;font-size:0.78rem;color:#555;line-height:1.6">
            💡 {outfit["style_note"]}<br><br>{outfit["color_tip"]}
        </div>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown('<p class="section-label">LOOK INSPIRATION</p>', unsafe_allow_html=True)
    ic1, ic2 = st.columns(2)
    with ic1: st.image(images[0], use_container_width=True)
    with ic2: st.image(images[1], use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">MOOD PLAYLIST</p>', unsafe_allow_html=True)
    for i, track in enumerate(music, 1):
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(track['query'])}"
        st.markdown(f"""
        <a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">
        <div class="music-card">
            <div class="music-idx">{i:02d}</div>
            <div style="flex:1">
                <div style="font-weight:500;font-size:0.9rem">{track["title"]}</div>
                <div style="font-size:0.75rem;color:#888;margin-top:2px">{track["artist"]}</div>
            </div>
            <div style="color:#aaa;font-size:0.8rem">▶ YouTube</div>
        </div></a>
        """, unsafe_allow_html=True)

st.markdown("<br>")
st.markdown('<div style="text-align:center;font-size:0.7rem;color:#bbb;padding:1.5rem 0;border-top:1px solid #E0DED8">WEATHERFIT · Powered by OpenWeatherMap & Unsplash</div>', unsafe_allow_html=True)

from __future__ import annotations

import re
import io
from collections import Counter
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

st.set_page_config(page_title="유튜브 댓글 분석 대시보드", page_icon="📊", layout="wide")

# ---------------------------------------------------------------------------
# 유틸 함수
# ---------------------------------------------------------------------------

def extract_video_id(url: str) -> str | None:
    """다양한 형태의 유튜브 URL에서 video ID를 추출한다."""
    url = url.strip()
    patterns = [
        r"(?:v=|/videos/|embed/|youtu\.be/|/shorts/|/live/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    return None


STOPWORDS = set("""
그리고 그런데 근데 진짜 너무 정말 그냥 아니 이건 저는 나는 제가 이게 그게 우리
이런 저런 하는 있는 없는 것을 것은 하고 에서 으로 이다 입니다 합니다 있다 없다
하다 되다 되는 이렇게 그렇게 저렇게 같은 같아요 같아 그래서 그리고 하지만 그러나
영상 채널 구독 좋아요 댓글 사람 우리는 나도 저도 이거 저거 거기 여기 저기
the a an is are was were to of and in on for with this that it its as be by at
you your i my we our they their he she his her not but or if so
""".split())

POSITIVE_WORDS = set("""
좋아요 좋다 좋은 최고 감사 사랑 웃긴다 대박 재밌다 재밌어요 멋지다 훌륭하다
고맙다 굿 굿굿 짱 응원 행복 힐링 감동 완벽 최애 갓
good great love awesome amazing nice happy thanks thank excellent perfect
best cool wonderful beautiful fantastic lol haha funny
""".split())

NEGATIVE_WORDS = set("""
싫어요 싫다 별로 최악 짜증 실망 나쁘다 나쁜 화나다 슬프다 짜증나 지루 노잼
답답 별로예요 최악이다 후회 실망스럽다
bad terrible worst hate awful sad angry boring disappointing sucks trash
worst annoying stupid ugly
""".split())

TOKEN_RE = re.compile(r"[가-힣]+|[A-Za-z]+")


def tokenize(text: str):
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    tokens = TOKEN_RE.findall(text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def simple_sentiment(text: str) -> str:
    tokens = set(tokenize(text))
    pos = len(tokens & POSITIVE_WORDS)
    neg = len(tokens & NEGATIVE_WORDS)
    if pos > neg:
        return "긍정"
    elif neg > pos:
        return "부정"
    return "중립"


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_video_info(api_key: str, video_id: str):
    youtube = build("youtube", "v3", developerKey=api_key)
    res = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
    if not res.get("items"):
        return None
    item = res["items"][0]
    return {
        "title": item["snippet"]["title"],
        "channel": item["snippet"]["channelTitle"],
        "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
        "published_at": item["snippet"]["publishedAt"],
        "view_count": int(item["statistics"].get("viewCount", 0)),
        "like_count": int(item["statistics"].get("likeCount", 0)),
        "comment_count": int(item["statistics"].get("commentCount", 0)),
    }


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_comments(api_key: str, video_id: str, max_comments: int, order: str):
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    page_token = None

    while len(comments) < max_comments:
        req = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, max_comments - len(comments)),
            order=order,
            textFormat="plainText",
            pageToken=page_token,
        )
        res = req.execute()

        for item in res.get("items", []):
            sn = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": sn.get("authorDisplayName", ""),
                "text": sn.get("textDisplay", ""),
                "like_count": sn.get("likeCount", 0),
                "published_at": sn.get("publishedAt", ""),
                "reply_count": item["snippet"].get("totalReplyCount", 0),
            })

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return comments


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("📊 유튜브 댓글 분석 대시보드")
st.caption("YouTube Data API 키와 영상 링크를 입력하면 댓글을 수집해서 분석해드려요.")

with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("YouTube Data API 키", type="password", help="Google Cloud Console에서 발급받은 API 키를 입력하세요.")
    video_url = st.text_input("영상 링크 또는 ID", placeholder="https://www.youtube.com/watch?v=...")
    max_comments = st.slider("가져올 댓글 수", min_value=50, max_value=1000, value=200, step=50)
    order = st.selectbox("정렬 기준", options=["relevance", "time"], format_func=lambda x: "관련도순" if x == "relevance" else "최신순")
    run = st.button("🔍 분석 시작", type="primary", use_container_width=True)

    with st.expander("API 키는 어떻게 받나요?"):
        st.markdown(
            "1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성\n"
            "2. **API 및 서비스 > 라이브러리**에서 'YouTube Data API v3' 검색 후 사용 설정\n"
            "3. **API 및 서비스 > 사용자 인증 정보**에서 API 키 발급\n"
            "4. 발급받은 키를 위 입력창에 붙여넣기"
        )

if not run:
    st.info("왼쪽 사이드바에 API 키와 영상 링크를 입력하고 **분석 시작** 버튼을 눌러주세요.")
    st.stop()

if not api_key:
    st.error("API 키를 입력해주세요.")
    st.stop()

video_id = extract_video_id(video_url) if video_url else None
if not video_id:
    st.error("올바른 유튜브 영상 링크 또는 ID를 입력해주세요.")
    st.stop()

# ---------------------------------------------------------------------------
# 데이터 조회
# ---------------------------------------------------------------------------

try:
    with st.spinner("영상 정보를 불러오는 중..."):
        info = fetch_video_info(api_key, video_id)
    if info is None:
        st.error("영상을 찾을 수 없습니다. 링크를 확인해주세요.")
        st.stop()

    with st.spinner(f"댓글을 최대 {max_comments}개 불러오는 중..."):
        raw_comments = fetch_comments(api_key, video_id, max_comments, order)

except HttpError as e:
    status = getattr(e.resp, "status", None)
    if status == 403:
        st.error("API 키가 유효하지 않거나 할당량(quota)이 초과되었거나, 댓글이 비활성화된 영상일 수 있습니다.")
    elif status == 404:
        st.error("영상을 찾을 수 없습니다.")
    else:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
    st.stop()
except Exception as e:
    st.error(f"알 수 없는 오류가 발생했습니다: {e}")
    st.stop()

if not raw_comments:
    st.warning("댓글이 없거나 댓글이 비활성화된 영상입니다.")
    st.stop()

df = pd.DataFrame(raw_comments)
df["published_at"] = pd.to_datetime(df["published_at"])
df["date"] = df["published_at"].dt.date
df["sentiment"] = df["text"].apply(simple_sentiment)

# ---------------------------------------------------------------------------
# 영상 정보 헤더
# ---------------------------------------------------------------------------

col_thumb, col_meta = st.columns([1, 3])
with col_thumb:
    st.image(info["thumbnail"])
with col_meta:
    st.subheader(info["title"])
    st.caption(f"채널: {info['channel']}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("조회수", f"{info['view_count']:,}")
    m2.metric("좋아요", f"{info['like_count']:,}")
    m3.metric("전체 댓글수", f"{info['comment_count']:,}")
    m4.metric("분석한 댓글수", f"{len(df):,}")

st.markdown("---")

# ---------------------------------------------------------------------------
# 감성 분석
# ---------------------------------------------------------------------------

st.subheader("💬 감성 분석 (키워드 기반 간이 분석)")
st.caption("긍정/부정 단어 사전을 기반으로 한 간단한 추정치이며, 정확한 감성 분석과는 차이가 있을 수 있어요.")

sent_col1, sent_col2 = st.columns([1, 2])
sent_counts = df["sentiment"].value_counts().reindex(["긍정", "중립", "부정"]).fillna(0)

with sent_col1:
    fig_pie = px.pie(
        names=sent_counts.index,
        values=sent_counts.values,
        color=sent_counts.index,
        color_discrete_map={"긍정": "#4CAF50", "중립": "#9E9E9E", "부정": "#F44336"},
        hole=0.4,
    )
    fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
    st.plotly_chart(fig_pie, use_container_width=True)

with sent_col2:
    for label, emoji in [("긍정", "😊"), ("중립", "😐"), ("부정", "😠")]:
        count = int(sent_counts.get(label, 0))
        pct = count / len(df) * 100 if len(df) else 0
        st.write(f"{emoji} **{label}**: {count}개 ({pct:.1f}%)")
        st.progress(min(pct / 100, 1.0))

st.markdown("---")

# ---------------------------------------------------------------------------
# 시간대별 댓글 추이
# ---------------------------------------------------------------------------

st.subheader("📅 날짜별 댓글 추이")
daily = df.groupby("date").size().reset_index(name="댓글수")
fig_time = px.bar(daily, x="date", y="댓글수")
fig_time.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320, xaxis_title="날짜", yaxis_title="댓글 수")
st.plotly_chart(fig_time, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# 자주 등장한 단어
# ---------------------------------------------------------------------------

st.subheader("🔤 자주 등장한 단어 Top 20")
all_tokens = []
for t in df["text"]:
    all_tokens.extend(tokenize(t))

if all_tokens:
    word_counts = Counter(all_tokens).most_common(20)
    word_df = pd.DataFrame(word_counts, columns=["단어", "빈도"]).sort_values("빈도")
    fig_words = px.bar(word_df, x="빈도", y="단어", orientation="h")
    fig_words.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=500)
    st.plotly_chart(fig_words, use_container_width=True)
else:
    st.info("분석할 단어가 충분하지 않습니다.")

st.markdown("---")

# ---------------------------------------------------------------------------
# 인기 댓글 & 원본 데이터
# ---------------------------------------------------------------------------

st.subheader("🏆 좋아요 많은 댓글 Top 10")
top_comments = df.sort_values("like_count", ascending=False).head(10)
for _, row in top_comments.iterrows():
    st.markdown(f"**👤 {row['author']}** · 👍 {row['like_count']} · {row['sentiment']}")
    st.write(row["text"])
    st.caption(row["published_at"].strftime("%Y-%m-%d %H:%M"))
    st.divider()

st.subheader("📋 전체 댓글 데이터")
st.dataframe(
    df[["author", "text", "like_count", "reply_count", "sentiment", "published_at"]],
    use_container_width=True,
    height=350,
)

csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
st.download_button(
    "📥 CSV로 다운로드",
    data=csv_buffer.getvalue(),
    file_name=f"youtube_comments_{video_id}.csv",
    mime="text/csv",
)

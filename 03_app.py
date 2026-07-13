import streamlit as st
import anthropic

st.set_page_config(page_title="AI 심리테스트", page_icon="🧠", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
* { font-family: 'Noto Sans KR', sans-serif; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); min-height: 100vh; }
[data-testid="stHeader"] { background: transparent; }
.title-box { text-align: center; padding: 2.5rem 0 1.5rem; }
.title-emoji { font-size: 3.5rem; }
.title-text { font-size: 2rem; font-weight: 700; color: #fff; margin: 0.5rem 0 0.2rem; }
.title-sub { font-size: 0.85rem; color: #aaa; letter-spacing: 0.1em; }
.q-card {
    background: rgba(255,255,255,0.07);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1rem;
}
.q-number { font-size: 0.7rem; letter-spacing: 0.2em; color: #a78bfa; margin-bottom: 0.4rem; text-transform: uppercase; }
.q-text { font-size: 1rem; font-weight: 500; color: #fff; line-height: 1.6; }
.result-card {
    background: rgba(167,139,250,0.1);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 16px;
    padding: 2rem;
    margin-top: 1.5rem;
}
.result-title { font-size: 1.3rem; font-weight: 700; color: #c4b5fd; margin-bottom: 1rem; }
.result-body { font-size: 0.9rem; color: #e2e8f0; line-height: 1.9; white-space: pre-wrap; }
div[data-testid="stRadio"] label { color: #ddd !important; font-size: 0.9rem; }
div[data-testid="stRadio"] > div { gap: 0.4rem; }
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #7c3aed, #a855f7);
    color: white;
    border: none;
    border-radius: 30px;
    padding: 0.8rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin-top: 1rem;
}
.stButton > button:hover { background: linear-gradient(135deg, #6d28d9, #9333ea); }
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 12px;
    color: white;
    padding: 0.7rem 1rem;
}
.stProgress > div > div { background: linear-gradient(90deg, #7c3aed, #a855f7); }
</style>
""", unsafe_allow_html=True)

QUESTIONS = [
    {
        "q": "주말 오전, 아무 계획이 없다. 나는?",
        "opts": ["늦잠 자다가 자연스럽게 일어난다", "일찍 일어나서 할 일 목록을 짠다", "친구한테 연락해서 약속을 잡는다", "유튜브 틀어놓고 뒹굴거린다"]
    },
    {
        "q": "대화할 때 나는 주로?",
        "opts": ["듣는 편이다, 상대방 말을 잘 들어준다", "말하는 편이다, 이야기 주도하는 게 편하다", "상황따라 다르다, 분위기 읽으면서 맞춘다", "생각 정리되면 말한다, 즉흥 발언은 잘 못한다"]
    },
    {
        "q": "스트레스 받을 때 가장 먼저 하는 행동은?",
        "opts": ["혼자 있고 싶다, 조용히 생각 정리", "친한 사람한테 털어놓는다", "운동이나 산책으로 해소한다", "뭔가를 먹거나 즐거운 거 본다"]
    },
    {
        "q": "새로운 카페에 갔는데 메뉴가 너무 많다. 나는?",
        "opts": ["늘 먹던 거 시킨다, 검증된 게 최고", "가장 특이한 메뉴 골라본다", "직원한테 추천 물어본다", "오래 고민하다가 결국 아무거나 시킨다"]
    },
    {
        "q": "친구가 갑자기 여행 가자고 한다. 내 반응은?",
        "opts": ["언제? 어디? 바로 찾아본다 (설렘)", "좋긴 한데... 일정 괜찮나 확인 먼저", "계획 짜는 것부터 시작하자 제안", "즉흥 여행은 좀 부담, 나중에 제대로 가자"]
    },
    {
        "q": "내가 가장 중요하게 생각하는 가치는?",
        "opts": ["자유 — 내 방식대로 살고 싶다", "안정 — 예측 가능한 삶이 좋다", "성장 — 계속 배우고 발전하고 싶다", "관계 — 사람들과 잘 지내는 게 최우선"]
    },
    {
        "q": "팀 프로젝트에서 나는 주로?",
        "opts": ["아이디어 내는 사람", "계획 짜고 정리하는 사람", "분위기 띄우고 중재하는 사람", "묵묵히 내 몫 다 하는 사람"]
    },
    {
        "q": "지금 내 방/공간 상태는?",
        "opts": ["항상 정리돼 있다, 어지러우면 불안함", "나름의 법칙이 있는 창의적 카오스", "대충 쓸만하면 됐지 뭐", "청소하려다 다른 거 하고 있음"]
    },
    {
        "q": "결정을 내릴 때 나는?",
        "opts": ["데이터·정보 충분히 모은 뒤 결정", "직관과 느낌으로 바로 결정", "주변 사람 의견 들어보고 결정", "계속 미루다가 상황이 결정해줌"]
    },
    {
        "q": "10년 후 나의 이상적인 모습은?",
        "opts": ["내 사업이나 분야에서 전문가로 인정받는 삶", "돈 걱정 없이 하고 싶은 거 하는 자유로운 삶", "사랑하는 사람들과 평화롭게 사는 삶", "세상에 의미 있는 영향을 남기는 삶"]
    },
]

# ── Header ──
st.markdown("""
<div class="title-box">
    <div class="title-emoji">🧠</div>
    <div class="title-text">AI 심리테스트</div>
    <div class="title-sub">10가지 질문으로 알아보는 나의 성격 유형</div>
</div>
""", unsafe_allow_html=True)

# ── Name input ──
name = st.text_input("", placeholder="이름 또는 닉네임 (선택사항)", label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# ── Questions ──
answers = []
all_answered = True

for i, item in enumerate(QUESTIONS):
    st.markdown(f"""
    <div class="q-card">
        <div class="q-number">Q {i+1:02d} / 10</div>
        <div class="q-text">{item["q"]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    ans = st.radio("", item["opts"], key=f"q{i}", index=None, label_visibility="collapsed")
    answers.append(ans)
    
    if ans is None:
        all_answered = False
    
    # 진행률
    answered_count = sum(1 for a in answers if a is not None)
    st.progress(answered_count / 10)
    st.markdown("<br>", unsafe_allow_html=True)

# ── Submit ──
if st.button("🔮 AI 분석 시작하기"):
    if not all_answered:
        st.warning("⚠️ 모든 질문에 답해주세요!")
    else:
        user_name = name if name else "당신"
        
        # 답변 정리
        qa_text = "\n".join([
            f"Q{i+1}. {QUESTIONS[i]['q']}\n답변: {answers[i]}"
            for i in range(10)
        ])
        
        prompt = f"""
다음은 {user_name}의 심리테스트 답변입니다.

{qa_text}

위 답변을 바탕으로 아래 항목을 분석해주세요. 따뜻하고 공감가며 재미있게 작성해주세요.

1. 🌟 성격 유형 (한 줄 타이틀 + 설명 3-4줄)
2. 💼 어울리는 직업/직무 (3가지, 이유 포함)
3. 💕 연애 스타일 (3-4줄)
4. ⚡ 강점 & 주의할 점 (각 2가지씩)
5. 🎯 {user_name}에게 보내는 한마디 (따뜻하고 힘나는 메시지)

이모지 적극 활용하고, 분석은 구체적이고 공감가게 작성해주세요.
"""
        
        with st.spinner("🔮 AI가 분석 중이에요..."):
            try:
                client = anthropic.Anthropic()
                result = ""
                
                with client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    result_placeholder = st.empty()
                    for text in stream.text_stream:
                        result += text
                        result_placeholder.markdown(f"""
                        <div class="result-card">
                            <div class="result-title">🧠 {user_name}의 심리 분석 결과</div>
                            <div class="result-body">{result}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"분석 중 오류가 발생했어요: {e}")

st.markdown("<div style='text-align:center;font-size:0.7rem;color:#444;padding:3rem 0 1rem;'>AI 심리테스트 · Powered by Claude AI · 재미로 보는 분석입니다</div>", unsafe_allow_html=True)

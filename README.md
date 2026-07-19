# 🐛 지렁이 게임 (Streamlit)

HTML5 Canvas로 만든 지렁이(스네이크) 게임을 Streamlit 앱으로 감싼 프로젝트입니다.
방향키(또는 WASD)로 조작하고, 모바일에서는 스와이프로 조작할 수 있습니다.

## 로컬에서 실행하기

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501` 에서 게임을 즐길 수 있습니다.

## GitHub에 올리기

1. GitHub에서 새 저장소를 만듭니다. (예: `worm-game`)
2. 이 폴더의 파일들(`app.py`, `requirements.txt`, `README.md`)을 저장소에 push 합니다.

```bash
cd worm-game
git init
git add .
git commit -m "지렁이 게임 초기 커밋"
git branch -M main
git remote add origin https://github.com/<본인계정>/worm-game.git
git push -u origin main
```

## Streamlit Community Cloud로 배포하기 (무료)

1. https://share.streamlit.io 접속 후 GitHub 계정으로 로그인
2. **"New app"** 클릭
3. 방금 만든 저장소(`worm-game`), 브랜치(`main`), 메인 파일(`app.py`)을 선택
4. **"Deploy"** 클릭하면 몇 분 안에 `https://<앱이름>.streamlit.app` 형태의 공개 URL이 생성됩니다.

이후 GitHub 저장소에 새로 push할 때마다 배포된 앱이 자동으로 업데이트됩니다.

## 파일 구성

```
worm-game/
├── app.py            # Streamlit 앱 (게임 로직 포함, HTML/JS 캔버스 임베드)
├── requirements.txt  # 의존성 목록
└── README.md         # 이 문서
```

## 커스터마이징 팁

- `app.py` 안의 `GRID`, `setInterval(tick, 110)` 값을 바꾸면 칸 크기와 게임 속도를 조절할 수 있습니다.
- 최고 점수는 브라우저의 `localStorage`에 저장되므로 기기별로 따로 기록됩니다.

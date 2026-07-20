# 지역·테마별 관광지 추천 (TourAPI + Streamlit)

## 1. 서비스키 발급
1. https://www.data.go.kr 접속 후 회원가입/로그인
2. 검색창에 **"한국관광공사_국문 관광정보 서비스_GW"** 검색
3. [활용신청] 클릭 (승인은 보통 즉시~수 분 내 완료)
4. 마이페이지 > [데이터 활용] > [Open API 인증키 발급현황] 에서
   **일반 인증키(Decoding)** 값을 복사

## 2. 설치 및 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 3. 사용
- 사이드바에 발급받은 서비스키를 붙여넣습니다.
  (매번 입력하기 번거로우면 `.streamlit/secrets.toml` 파일에
  `TOUR_API_KEY = "발급받은키"` 를 넣어두면 자동으로 채워집니다.)
- 시/도 → 시/군/구 → 관광 타입(관광지, 축제/행사, 맛집 등 복수 선택 가능)을 고른 뒤
  **검색** 버튼을 누르면 지도에 마커로 표시되고 우측에 목록이 나옵니다.
- 마커 색상은 타입별로 다르게 표시됩니다 (관광지=초록, 축제=빨강, 음식점=하늘색 등).

## 참고
- API Base URL: `https://apis.data.go.kr/B551011/KorService2`
- 사용 엔드포인트: `areaCode2`(시군구 코드), `areaBasedList2`(지역기반 목록 조회)
- 한 번에 최대 100건까지 조회하도록 되어 있습니다 (`numOfRows` 값을 조정 가능).

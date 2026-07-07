---
name: travel-spot-reviews
description: Google Maps 리뷰 및 여행 커뮤니티 리뷰를 조회하여 관광 스팟별 실용적인 팁과 주의사항을 수집하고 Notion 페이지에 추가합니다. 웹 검색, Google Maps MCP, Chrome 스크래핑을 병행합니다. 사용자가 리뷰 조회, 관광지 후기, 구글 리뷰, 방문자 팁, 현지인 추천, 주의사항 확인, 평점 조회 등을 요청할 때 이 스킬을 사용하세요.
---

# Travel Spot Reviews

Google Maps 리뷰 및 여행 커뮤니티 후기를 수집하여, 각 관광 스팟의 실용적인 팁과 주의사항을 Notion 여행 가이드에 추가하는 스킬입니다.

## 핵심 원칙

- **3단계 리뷰 수집**: 웹 검색 → Google Maps MCP → Chrome 스크래핑 순서로 병행
- **실용 정보 중심**: 별점 나열이 아닌, 실제 방문자의 **구체적 팁과 주의사항** 추출
- **한국어 리뷰 우선**: 한국인 여행자 리뷰를 우선 수집, 영문 리뷰로 보완

## 수집 정보 카테고리

각 스팟에 대해 다음 7가지 정보를 수집합니다:

### 1. ⭐ 평점 요약

```
Google Maps 평점: 4.6/5 (12,345 리뷰)
TripAdvisor: 4.5/5 (#3 in Las Vegas Things to Do)
```

### 2. 👍 방문자 추천 팁 (Top Tips)

리뷰에서 반복적으로 언급되는 추천 사항:
- 구체적 장소/시간이 포함된 팁
- 최근 6개월 이내 리뷰 우선
- 최소 3회 이상 반복 언급된 내용

### 3. ⚠️ 주의사항 & 불만 사항

리뷰에서 반복적으로 언급되는 부정적 피드백:
- 안전 관련 주의사항
- 주차/혼잡도 관련
- 날씨/환경 관련

### 4. 👨‍👩‍👧 가족/아이 동반 후기

어린이 동반 방문자 리뷰 특별 수집:
- 연령대별 적합성
- 유모차/카시트 접근성
- 아이 프로그램/활동

### 5. 📸 사진 스팟 추천 (리뷰 기반)

방문자들이 추천하는 포토 스팟과 최적 촬영 시간

### 6. 🍽️ 근처 식당 리뷰

스팟 주변 식당의 실제 리뷰 (평점, 추천 메뉴, 대기 시간)

### 7. 🕐 방문 시간 추천

리뷰 기반 최적 방문 시간대, 피해야 할 시간, 평균 소요 시간

## 리뷰 수집 방법

### 방법 1: 웹 검색 (기본, 항상 실행)

```
WebSearch 쿼리 전략:

1. Google Maps 리뷰 요약
   "{스팟명} Google Maps reviews tips"
   "{스팟명} 구글 리뷰 팁 주의사항"
   "{스팟명} visitor tips what to know before"

2. 한국어 블로그 후기
   "{스팟명 한국어} 후기 팁"
   "{스팟명 한국어} 방문 주의사항"
   "{스팟명 한국어} 아이와 함께"

3. TripAdvisor / Yelp 요약
   "site:tripadvisor.com {스팟명} tips"
   "site:yelp.com {스팟명 근처 식당} reviews"

4. Reddit 여행 팁
   "site:reddit.com {스팟명} tips advice"
   "site:reddit.com r/travel {여행지} must know"
```

### 방법 2: Google Maps MCP (있으면 활용)

```
.mcp.json에 Google Maps MCP가 설정된 경우:

1. 스팟 검색 → place_id 획득
2. 상세 정보 조회 → rating, reviews, opening_hours
3. 리뷰 분석
   - 최신 리뷰 50개 분석
   - 반복 키워드 추출
   - 긍정/부정 분류
   - 가족 관련 리뷰 필터
4. 근처 식당 검색 → 평점 상위 5곳 + 리뷰 요약
```

### 방법 3: Chrome 스크래핑 (보완)

```
웹 검색과 MCP로 충분한 정보를 얻지 못한 경우:

1. Google Maps 페이지 접근
   navigate("https://www.google.com/maps/search/{스팟명}")
2. 리뷰 섹션 읽기
   get_page_text() → 리뷰 텍스트 추출
3. TripAdvisor 페이지 보완
   navigate("https://www.tripadvisor.com/Search?q={스팟명}")
4. 정보 구조화
```

## 리뷰 분석 & 필터링

### 유용한 리뷰 판별 기준

```
높은 가치:
✅ 구체적 장소/시간 언급 ("오전 7시에 가면 주차 가능")
✅ 실용적 팁 ("입구에서 지도 꼭 받기")
✅ 최근 리뷰 (6개월 이내)
✅ 사진 첨부 리뷰
✅ 아이 동반 경험

낮은 가치:
❌ "좋았어요" 등 단순 감상
❌ 별점만 있고 텍스트 없는 리뷰
❌ 2년 이상 된 오래된 리뷰
❌ 스팟과 무관한 내용
```

### 반복 패턴 추출

```
같은 내용이 3회 이상 언급되면 '주요 팁'으로 분류:
- "주차" 관련 → 🅿️ 주차 팁
- "시간/대기" 관련 → ⏰ 방문 시간 팁
- "날씨/온도" 관련 → 🌡️ 날씨 주의
- "아이/가족" 관련 → 👨‍👩‍👧 가족 팁
- "음식/식당" 관련 → 🍽️ 식사 팁
- "사진/뷰" 관련 → 📸 포토 팁
- "위험/안전" 관련 → ⚠️ 안전 주의
```

## Notion 페이지 반영

### 삽입 형식

각 스팟 섹션에 리뷰 기반 블록을 추가:

```markdown
> 🗣️ **방문자 리뷰 하이라이트** (Google Maps ⭐4.6, 12K+ 리뷰)
>
> **👍 추천 팁:**
> • 새벽 일출 시간 방문 추천 — 인파 적고 최고의 사진
> • Bright Angel Trail 입구 주차장은 오전 7시 전 도착 필요
> • Junior Ranger 프로그램 무료, 아이에게 강추
>
> **⚠️ 주의사항:**
> • 여름 기온 45°C 이상, 물 2L+ 필수 휴대
> • 가드레일 없는 구간 다수 — 아이 동반 시 각별히 주의
> • 주차장 오전 10시 만차 빈번 → 셔틀버스 이용 권장
>
> **🕐 추천 방문 시간:** 오전 6-8시 또는 오후 4-6시
> **⏱️ 평균 소요 시간:** 2-3시간 (전체 투어 5-6시간)
```

### 삽입 위치

기존 콘텐츠 보강 블록(travel-content-enrichment) 이후에 추가:

```
## 📍 {스팟명}
![이미지](url)
{스팟 설명}
{정보 테이블}

> 🌍 **역사/문화** ...
> 👨‍👩‍👧 **아이와 함께하는 팁** ...
> 📸 **포토 스팟** ...
> 🍽️ **맛집** ...
> 💰 **예상 비용** ...
> 🔍 **블로그 검색어** ...

> 🗣️ **방문자 리뷰 하이라이트** ...  ← 여기에 추가

---
```

## 파이프라인 통합

### 오케스트레이터에서의 위치

```
④ travel-content-enrichment — 6가지 상세 콘텐츠 보강
    ↓
④-1 travel-spot-reviews — 리뷰 기반 팁/주의사항 추가 ← 여기
    ↓
⑤ travel-calendar-sync — Google Calendar 이벤트 생성
```

### 병렬 처리

- 날짜별로 Agent를 분배하여 병렬 리뷰 수집 가능
- 각 Agent가 담당 날짜의 스팟들에 대한 리뷰를 수집
- 수집 후 Notion 업데이트는 순차 처리 (API 제한)

### 입출력

```
입력:
  - spot_list: [{name, name_en, page_id, section_marker}]
  - travel_type: road_trip | city | beach | nature
  - family_info: {adults: N, children: [{age: N}]}

출력:
  - reviews_data: /tmp/{여행지}_reviews.json
  - updated_pages: Notion 페이지 업데이트 완료
  - review_summary: 전체 리뷰 수집 요약
```

## Google Maps MCP 설정

`.mcp.json`에 Google Maps MCP를 추가하려면:

```json
{
  "mcpServers": {
    "google-maps": {
      "type": "sse",
      "url": "https://mcp.composio.dev/partner/composio/google-maps/mcp",
      "note": "Google Maps Place Details & Reviews API"
    }
  }
}
```

> **참고**: Google Maps MCP가 없어도 웹 검색 + Chrome 스크래핑으로 기본 기능 동작

## 오류 처리

| 상황 | 대응 |
|------|------|
| 웹 검색 결과 부족 | 검색 키워드 변경 (영문/한국어 전환) 후 재시도 |
| Google Maps MCP 미연결 | 웹 검색 + Chrome으로 대체 |
| Chrome 스크래핑 차단 | 웹 검색 결과만으로 진행 |
| 리뷰 수 부족 (< 5개) | "리뷰 정보가 제한적입니다" 명시 |
| Notion 업데이트 실패 | 페이지 재fetch 후 재시도, 실패 시 스킵 |
| 특정 스팟 리뷰 없음 | 해당 스팟 리뷰 블록 생략, 보고서에 기록 |

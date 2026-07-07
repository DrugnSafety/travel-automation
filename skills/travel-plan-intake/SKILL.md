---
name: travel-plan-intake
description: 여행 계획 수립의 진입점입니다. 사용자가 구체적인 여행 계획(일정표, 예약 확인서, 메모)을 입력하거나 파일을 업로드하면 이를 파싱해 표준 여행 계획 JSON으로 변환하고, 아무 자료가 없으면 대화형 인터뷰로 취향·제약을 파악한 뒤 Claude가 여행 계획을 직접 창조합니다. 사용자가 여행 가고 싶어, 여행 계획 세워줘, 일정 짜줘, 이 파일로 여행 준비해줘 등을 요청할 때 파이프라인의 첫 단계로 반드시 이 스킬을 사용하세요.
---

# Travel Plan Intake

모든 여행 자동화 파이프라인의 **첫 단계**. 사용자 자료가 있으면 100% 활용하고, 없으면 대화로 파악한 뒤 여행 계획을 창조한다. 결과물은 표준 여행 계획 JSON으로, 이후 모든 스킬(research → notion → images → calendar → ppt)의 단일 입력(source of truth)이 된다.

## 분기 판정 (가장 먼저)

```
① 사용자가 파일을 업로드했거나 경로를 언급 → [모드 A: 자료 파싱]
② 메시지 안에 날짜·목적지·동선이 이미 구체적으로 있음 → [모드 A: 텍스트 파싱]
③ "어디 갈까", "여행 가고 싶어" 수준의 막연한 요청 → [모드 B: 대화형 창조]
④ 목적지만 있고 일정이 없음 ("4월에 그랜드캐년") → [모드 B-단축: 핵심 질문 후 창조]
```

판정이 애매하면 AskUserQuestion으로 "가지고 계신 일정/예약 자료가 있나요?"를 먼저 묻는다.
- 옵션: 1) 파일 업로드 2) 텍스트로 붙여넣기 3) 자료 없음 — 대화로 계획 수립

## 모드 A: 사용자 자료 파싱

### 지원 입력
| 형태 | 처리 |
|------|------|
| 텍스트 일정 (채팅 붙여넣기) | 직접 파싱 |
| Markdown/TXT 파일 | Read 후 파싱 |
| PDF (항공권·바우처·투어 확인서) | Read(pages)로 읽고 travel-transport-info와 연계 파싱 |
| 이미지 (예약 스크린샷) | Read로 시각 판독 |
| DOCX/XLSX | 변환 도구 또는 텍스트 추출 후 파싱 |
| Notion/Google Docs URL | Notion fetch / Google Drive MCP로 읽기 |
| 구글맵/네이버지도 저장 리스트 URL | travel-maps-integration의 리스트 임포트로 스팟 추출 |
| Gmail 예약 메일 | Gmail MCP search_threads("예약 OR confirmation")로 수집 (사용자 동의 후) |

### 파싱 원칙
1. **사용자 자료가 항상 우선** — Claude가 임의로 일정·시간·장소를 바꾸지 않는다. 개선 제안은 파싱 완료 후 별도 섹션으로만 제시.
2. 누락 필드(숙소 미정, 이동수단 불명 등)는 `"TBD"`로 표기하고 마지막에 한 번에 질문.
3. 상대 날짜("다음 달", "여름방학")는 절대 날짜로 변환 후 사용자에게 확인.
4. 기존 메모리(`user_travel_*`)와 프로젝트 폴더 내 동일 여행 파일을 검색해 병합 — 충돌 시 사용자 확인.

## 모드 B: 대화형 계획 창조

자료가 없으면 AskUserQuestion으로 **한 번에 최대 4개 질문**, 최대 2라운드로 파악한다:

### 라운드 1 (필수)
- 목적지 (미정이면 계절·비행시간·예산 힌트로 3개 후보 제안)
- 여행 기간·시기 (몇 박, 유연한지)
- 인원 구성 (기본값: 성인 2 + 자녀 1, 메모리의 가족 정보 활용)
- 여행 스타일 (자동차 로드트립 / 도시 관광 / 휴양 / 국립공원 — 기본값: 가족 로드트립)

### 라운드 2 (선택 — 라운드 1 답변에 따라)
- 예산 수준, 숙소 취향 (호텔/캠핑/RV), 필수 포함 스팟, 페이스 (빡빡하게/느긋하게)

### 계획 창조 규칙
1. WebSearch로 최신 정보(운영시간·예약 오픈·계절 조건) 확인 후 일정 설계 — 추측 금지, 출처 URL 보관.
2. 하루 이동시간 상한: 아이 동반 시 운전 4시간/일, 도보 5km/일 (초등 4학년 기준).
3. 국립공원 방문 시 Junior Ranger 프로그램을 일정에 명시적으로 포함.
4. 각 Day에 백업 플랜(우천/폐쇄 시 대안) 1개 포함.
5. 완성된 초안은 반드시 사용자에게 **요약 테이블로 승인**을 받은 뒤 다음 단계로 진행.

## 출력: 표준 여행 계획 JSON

`/tmp/{여행지}_plan.json`으로 저장. 이후 모든 스킬이 이 파일을 읽는다.

```json
{
  "trip_name": "2026 그랜드캐년 & 유타",
  "emoji": "🏜️",
  "origin": "Boston, MA",
  "start_date": "2026-04-15", "end_date": "2026-04-26",
  "party": {"adults": 2, "children": [{"name": "서현", "age": 10, "grade": "초4"}]},
  "style": "RV 로드트립 / 국립공원",
  "source": "user_file | user_text | claude_generated",
  "source_files": ["원본 파일 경로"],
  "days": [
    {
      "day": 1, "date": "2026-04-15", "region": "Las Vegas",
      "route": {"from": "LAS 공항", "to": "호텔", "drive_km": 12, "drive_min": 20},
      "spots": [
        {"name": "Bellagio Fountains", "name_ko": "벨라지오 분수쇼",
         "type": "landmark", "reservation": null,
         "gmaps_query": "Bellagio Fountains Las Vegas",
         "wiki_title": "Fountains of Bellagio"}
      ],
      "lodging": {"name": "...", "status": "booked|TBD", "confirmation": "..."},
      "meals": [], "notes": ""
    }
  ],
  "transport": {"flights": [], "rental_car": null},
  "reservations_needed": [],
  "open_questions": ["TBD 항목 목록"]
}
```

**스팟마다 `gmaps_query`(구글맵 검색어)와 `wiki_title`(영문 위키피디아 문서명)을 반드시 채운다** — 이후 travel-maps-integration과 travel-image-search가 그대로 사용한다. wiki_title이 불확실하면 `https://en.wikipedia.org/api/rest_v1/page/summary/{제목}`을 curl로 호출해 실존 여부를 확인한다.

## 완료 후 라우팅

1. JSON 저장 → 사용자에게 요약 테이블 제시 (Day/날짜/지역/핵심/숙박)
2. "전체 자동화"였다면 → travel-orchestrator로 연결
3. 단일 요청(노션만, 캘린더만)이었다면 → 해당 스킬로 직행하며 JSON 경로 전달
4. 메모리 갱신: 확정된 일정은 `user_travel_*` 메모리에 절대 날짜로 저장

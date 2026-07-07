---
name: travel-maps-integration
description: Google Maps를 여행 가이드 전반에 연계합니다. 스팟별 구글맵 바로가기 링크, Day별 경유지 포함 경로 링크, 이동 거리·시간 검증, 평점·운영시간 조회를 수행하고 Notion·Calendar에 딥링크를 심습니다. 사용자가 구글맵 연동, 지도 링크, 경로 만들어줘, 내비 링크, 이동 시간 확인 등을 요청할 때 이 스킬을 사용하세요.
---

# Travel Maps Integration

Google Maps를 **API 키 없이도** 최대한 활용하는 스킬. 핵심 산출물은 ① 스팟별 지도 딥링크 ② Day별 전체 경로 딥링크 ③ 이동 시간 검증 데이터.

## 1. 스팟별 지도 딥링크 (Universal Maps URL — 키 불필요, 전 플랫폼 동작)

plan JSON의 `gmaps_query`로 표준 URL 생성:

```
검색:   https://www.google.com/maps/search/?api=1&query={URL인코딩된 장소명+지역}
장소ID: https://www.google.com/maps/search/?api=1&query={장소명}&query_place_id={place_id}
```

- 쿼리는 반드시 `장소명 + 도시/주`로 구체화 (예: `Horseshoe Bend, Page, AZ`) — 동명 장소 오매칭 방지
- Notion 스팟 섹션의 기본정보 테이블에 `📍 지도` 행으로 삽입: `[Google Maps에서 열기]({URL})`
- Google Calendar 이벤트의 location 필드에는 장소명+주소 문자열을 넣고, description에 딥링크 추가

## 2. Day별 경로 딥링크 (경유지 포함 — 현지에서 바로 내비 시작)

```
https://www.google.com/maps/dir/?api=1
  &origin={출발지}
  &destination={최종 목적지}
  &waypoints={경유지1}|{경유지2}|{경유지3}
  &travelmode=driving
```

- 경유지 최대 9개 (URL 한계). 스팟이 더 많으면 오전/오후 2개 링크로 분할
- 각 Day 페이지 "🚗 이동 시간표" 섹션 상단에 `[🗺️ 오늘 전체 경로 열기]({URL})` 배치
- 메인 페이지 "🗺️ 한눈에 보기" 섹션에 Day별 경로 링크 테이블 추가

## 3. 이동 거리·시간 검증

일정의 이동 시간이 현실적인지 검증한다 (아이 동반 일정의 핵심 품질 요소):

```
우선순위:
① Google Maps MCP 연결 시: directions/distance 조회
② WebSearch: "driving time {A} to {B}" — 최소 2개 출처 교차 확인
③ Chrome MCP: google.com/maps/dir/{A}/{B} 페이지를 열어 소요시간 텍스트 읽기
```

- 검증 결과가 plan JSON의 `drive_min`과 20% 이상 차이나면 사용자에게 경고 + 일정 조정 제안
- 결과를 plan JSON에 `verified_drive_min` 필드로 기록 (출처 병기)

## 4. 평점·운영시간·리뷰 (travel-spot-reviews와 연계)

- Google Maps MCP가 연결되어 있으면: place details로 평점·리뷰수·운영시간 → 스팟 기본정보 테이블에 반영
- 없으면: WebSearch로 `"{스팟명}" hours rating` 조회 후 공식 사이트로 교차 확인, Chrome MCP 스크래핑 보완
- 심층 리뷰 분석(팁·주의사항 추출)은 travel-spot-reviews 스킬 담당 — 중복 수집하지 않는다

## 5. 지도 저장 리스트 임포트 (TREK 방식 차용)

사용자가 구글맵/네이버지도에 저장해 둔 장소 리스트 URL을 주면 스팟 목록으로 자동 변환한다:

### 구글맵 공유 리스트
1. `goo.gl`/`maps.app.goo.gl` 단축링크는 `curl -sI`로 리다이렉트를 추적해 원본 URL 확보
2. WebFetch 또는 Chrome MCP로 리스트 페이지를 열어 장소명·좌표·메모 추출
3. 개별 공유 링크는 URL 좌표(`@lat,lng`) 또는 장소명으로 해석

### 네이버지도 저장 폴더
1. `naver.me` 단축링크 해제 → 폴더 공유 URL 확보
2. 북마크 공유 API로 목록 조회 (TREK 검증 엔드포인트):
   `https://pages.map.naver.com/save-pages/api/maps-bookmark/v3/shares/{공유ID}?limit=20&placeInfo=true&sort=lastUseTime&mcids=ALL` (페이지네이션)
3. 응답에서 `name`, `py`(위도), `px`(경도), `memo`, `address` 추출
4. API 실패 시 Chrome MCP로 공유 페이지를 직접 열어 읽기

### 공통 후처리
- 좌표 근접(±0.0001, 약 11m) + 정규화 이름으로 중복 제거
- 추출된 스팟은 plan JSON의 `spots`로 병합 → travel-plan-intake에 전달
- 각 스팟의 메모(`memo`)는 사용자 의도이므로 Notion 스팟 섹션에 "💬 내 메모"로 보존

## 6. 날씨 연동 (Open-Meteo — 무료·키 불필요)

Day 페이지 "일자 개요" 날씨 자동 채움 (여행 16일 전부터 유효):
```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode&timezone=auto&start_date={날짜}&end_date={날짜}"
```
- 16일 이전 기획 단계에는 기후 평년값(웹 검색)으로 "🌡️ 기후 요약" 테이블을 채우고, 출발 1~2주 전 이 API로 실예보 갱신을 제안한다.

## 7. My Maps 커스텀 지도 (선택 — 사용자 요청 시)

전체 여행 스팟을 한 지도에 표시하고 싶을 때:
1. 스팟 목록을 CSV로 생성 (`name, address, day, note` 컬럼)
2. 사용자에게 CSV 전달 + Google My Maps 임포트 절차 안내 (mymaps.google.com → 만들기 → 가져오기)
3. 또는 Chrome MCP로 My Maps 생성 과정을 직접 자동화 (사용자 로그인 상태 필요)
4. 완성된 My Maps 공유 링크를 Notion 메인 페이지에 embed

## 6. 오프라인 대비 블록

각 여행 메인 페이지 교통 섹션에 자동 삽입:
- 오프라인 지도 다운로드 안내: Google Maps 앱 → 프로필 → 오프라인 지도 → 여행 지역 저장
- 국립공원 등 통신 불가 지역 목록 (리서치 결과 기반) + 종이 지도 대안

## 파이프라인 내 위치

notion-travel-page 직후 실행 — 페이지 골격이 생긴 뒤 지도 링크를 일괄 삽입하고, travel-calendar-sync가 이 스킬의 링크 데이터를 재사용한다. 산출물: `/tmp/{여행지}_maps.json` (spot별 딥링크 + Day별 경로 링크 + 검증된 이동시간).

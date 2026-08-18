---
name: travel-maps-integration
description: 여행 일정의 모든 장소를 좌표 기반으로 정리해 구글맵과 연동하는 스킬. 날짜별 노션 페이지에 임베드 지도와 모바일 내비 딥링크를 삽입하고, 장소별 좌표 링크 표를 만들며, Google My Maps로 일괄 임포트할 수 있는 KML과 CSV, 경로 URL 목록을 생성한다. 사용자가 구글맵 연동, 지도 추가, 경로 만들기, 내비 링크, 장소 저장, My Maps, KML, 동선 정리, 지도 페이지 등을 요청할 때 사용. 구글맵 개인 저장 목록에는 외부 API로 쓸 수 없다는 제약과 그 우회법을 함께 안내한다.
---

# Travel Maps Integration

## 먼저 알아야 할 제약

**구글맵의 개인 "저장됨(Saved)" 목록에 외부에서 장소를 추가하는 공개 API는 없다.** Google Places API는 읽기 전용이고, Google Maps JavaScript API에도 사용자 저장 목록 쓰기 기능이 없다. 브라우저 자동화로 별표를 누르는 방법은 봇 차단 때문에 실무에서 실패한다.

사용자가 "자동으로 내 구글맵에 저장 안 되나요?"라고 물으면 **이 사실을 먼저 알리고** 아래 대안을 제시한다.

| 방법 | 소요 | 결과 | 권장도 |
|---|---|---|---|
| **Google My Maps + KML 임포트** | 3분 | 전 장소가 Day별 폴더로 정리된 개인 지도. 휴대폰 구글맵 "저장됨 → 지도" 탭에 표시 | ⭐ 최선 |
| 앱에서 수동 별표 | 장소당 20초 | 기본 "저장됨" 목록에 들어감 | 핵심 장소만 |
| 브라우저 자동화 | — | 봇 차단으로 실패 | ❌ |

**이 안내는 작업 후반이 아니라 초기 질문 단계(`travel-intake` Q4-2)에서 해야 한다.**

---

## 산출물 5종

### 1. 날짜별 노션 페이지 지도 섹션

각 날짜 페이지 하단에 다음 블록을 `insert_content`로 추가한다.

````markdown
---

## 🗺️ Day {N} 지도

<embed src="https://maps.google.com/maps?saddr={출발lat},{출발lon}&daddr={경유다1}+to:{경유다2}+to:{도착}&output=embed">Day {N} 경로: {요약} (약 {거리}마일 / {시간})</embed>

📱 [**휴대폰에서 내비 시작하기 →**](https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={lat},{lon}&waypoints={lat},{lon}%7C{lat},{lon}&travelmode=driving)

### 개별 장소 바로가기

<table header-row="true">
<tr><td>장소</td><td>구글맵</td><td>메모</td></tr>
<tr><td>{이모지} {장소명}</td><td>[열기](https://www.google.com/maps/search/?api=1&query={lat},{lon})</td><td>{메모}</td></tr>
</table>
````

**임베드 지도는 API 키가 필요 없다.** `maps.google.com/maps?...&output=embed` 형식은 무료 공개 임베드다. `google.com/maps/embed/v1/`은 키가 필요하니 쓰지 않는다.

### 2. 모바일 딥링크 규칙

노션 모바일 앱에서 링크를 누르면 구글맵 앱이 열려야 한다. 다음 형식을 쓴다.

| 용도 | URL |
|---|---|
| 단일 장소 | `https://www.google.com/maps/search/?api=1&query={lat},{lon}` |
| 경로 | `https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={lat},{lon}&waypoints={lat},{lon}%7C{lat},{lon}&travelmode=driving` |
| 임베드 | `https://maps.google.com/maps?saddr=...&daddr=...+to:...&output=embed` |

주의사항:
- 마크다운 링크 안에서 waypoints 구분자 `|`는 **`%7C`로 인코딩**한다. 인코딩하지 않으면 표 문법과 충돌한다.
- 경유지는 **최대 9개**. 초과하면 핵심 지점만 넣고 나머지는 표로 제공한다.
- 좌표는 소수점 4자리면 약 11m 정밀도로 충분하다.

### 3. KML — Google My Maps 임포트용

Day별 `<Folder>` 구조로 생성한다. 카테고리별 아이콘·색상을 지정하면 지도가 한눈에 읽힌다.

```
scripts/build_map_assets.py --spots spots.json --out assets/
```

카테고리 → 아이콘 매핑 기본값:

| 카테고리 | 아이콘 | 색상 |
|---|---|---|
| 공항 | plane | 파랑 |
| 차량 (렌트/반납) | car | 회색 |
| 관문 (공원 입구) | gate | 갈색 |
| 숙박 | campground / lodging | 초록 |
| 관광 | camera | 빨간 |
| 야생동물 | paw | 주황 |
| 식당 | dining | 노랑 |
| 쇼핑 | shopping | 보라 |
| 주유·편의 | gas | 청록 |
| 경유 | dot | 흰색 |

### 4. CSV

**UTF-8 BOM**으로 저장한다. BOM이 없으면 한국어 Excel에서 한글이 깨진다.

컬럼: `Day, 장소명(한), 장소명(영), 위도, 경도, 카테고리, 메모, 구글맵링크`

### 5. 전체 지도·경로 노션 페이지

메인 페이지 하위에 독립 페이지를 만든다. 구성:

1. My Maps 임포트 3단계 안내
2. 자동 저장 제약 설명 표
3. 날짜별 경로 링크 표 (11개 행)
4. 전체 장소 표 (Day별 소제목 + 좌표 링크)
5. 첨부 파일 3종 설명

---

## 좌표 수집

### 우선순위

1. **공식 출처** — NPS 등 공공기관이 공개한 좌표
2. **연결된 MCP** — TomTom Maps(`tomtom-geocode`, `tomtom-poi-search`), Google Maps MCP
3. **웹 검색** — "{장소명} coordinates latitude longitude"
4. **지도 URL 파싱** — 구글맵 URL의 `@lat,lon,zoom` 구간

### 검증

수집한 모든 좌표는 여행 지역 바운딩 박스 안에 있어야 한다.

```python
BOX = {"n": 46.0, "s": 43.0, "w": -112.0, "e": -101.0}  # 예: 옥로스톤~배들랜즈
assert BOX["s"] <= lat <= BOX["n"] and BOX["w"] <= lon <= BOX["e"]
```

부호 누락(`-110` → `110`)이 가장 흔한 오류다. 서경은 반드시 음수다.

### pull-out과 전망대

국립공원의 전망대·야생동물 관찰 지점은 정식 주소가 없다. **이름 검색으로는 못 찾거나 엉뚱한 곳이 나온다.** 반드시 좌표로 지정한다.

또한 대형차 주차가 가능한 별도 트레일헤드가 있는 경우, **본 주차장이 아니라 그쪽 좌표를 준다.** (예: 그랜드프리즘매틱 본 주차장 대신 페어리폴스 트레일헤드)

---

## 스팟 데이터 스키마

```json
{
  "id": "grand-prismatic",
  "day": 2,
  "name_ko": "그랜드프리즘매틱",
  "name_en": "Grand Prismatic Spring",
  "lat": 44.5251, "lon": -110.8383,
  "category": "관광",
  "note": "미국 최대 온천 · 지름 112m",
  "parking": {
    "primary": {"lat": 44.5251, "lon": -110.8383, "rv_ok": false},
    "alternate": {"name": "Fairy Falls Trailhead", "lat": 44.5133, "lon": -110.8300, "rv_ok": true}
  },
  "best_time": "오전 10~12시 (수증기가 걸힌 뒤)",
  "arrival_order": 3
}
```

## 연동 가능한 MCP

`.mcp.json`에 정의되어 있으면 활용한다. 없으면 웹 검색으로 대체하고, 사용자에게 연결을 제안한다.

- **TomTom Maps** — 지오코딩, POI 검색, 경로 계산, 실시간 교통
- **Google Maps (Composio)** — 장소 상세, 리뷰, 영업시간
- **Felt Maps** — `create_map`, 레이어 관리 (공유 가능한 웹 지도)

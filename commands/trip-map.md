---
description: 여행 장소를 구글맵과 연동 (지도 임베드 · 내비 링크 · KML)
argument-hint: "[trip_slug 또는 노션 페이지 URL]"
---

사용자가 지도 연동을 요청했다. **`travel-maps-integration` 스킬**을 실행하라.

## 먼저 고지할 것

사용자가 "자동으로 내 구글맵에 저장" 을 기대할 수 있다. **작업 전에 알린다.**

> 구글은 개인 "저장됨(Saved)" 목록에 외부에서 장소를 추가하는 공개 API를 제공하지 않습니다. Places API는 읽기 전용입니다. 대신 **Google My Maps에 KML을 임포트**하면 전 장소를 3분 만에 한 번에 올릴 수 있고, 그 지도는 휴대폰 구글맵 앱의 "저장됨 → 지도" 탭에 나타납니다.

브라우저 자동화로 별표를 누르는 방법은 봇 차단으로 실패한다. 시도하지 않는다.

## 산출물 5종

1. **날짜별 노션 지도 섹션** — `insert_content`로 각 날짜 페이지 하단에 추가
   - `<embed src="https://maps.google.com/maps?saddr=...&daddr=...+to:...&output=embed">` (API 키 불필요)
   - 📱 모바일 내비 딥링크 (`maps/dir/?api=1&...`, waypoints 구분자는 `%7C`)
   - 스팟별 좌표 링크 표 (`maps/search/?api=1&query={lat},{lon}`)
2. **KML** — Day별 폴더, 카테고리별 아이콘·색상
3. **CSV** — UTF-8 BOM (없으면 한국어 Excel에서 깨진다)
4. **경로 URL 목록 (routes.md)**
5. **전체 지도·경로 노션 페이지** — 임포트 안내 + 날짜별 경로 표 + 전체 장소 표

## 스크립트

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/travel-maps-integration/scripts/build_map_assets.py \
  --spots /tmp/{trip_slug}/spots.json \
  --routes /tmp/{trip_slug}/routes.json \
  --out /tmp/{trip_slug}/assets \
  --title "{여행명}" \
  --box {s},{n},{w},{e}
```

`--box`를 주면 좌표 바운딩 박스를 검증해 부호 누락(`-110` → `110`)을 잡아낸다.

## 좌표 원칙

**모든 링크를 장소명이 아니라 위경도로 만든다.** 국립공원의 전망대와 pull-out은 정식 주소가 없어 이름 검색으로는 엉뚱한 곳이 나온다.

대형차 주차가 별도 트레일헤드에만 가능하면 **본 주차장이 아니라 그쪽 좌표**를 준다.

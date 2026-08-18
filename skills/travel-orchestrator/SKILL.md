---
name: travel-orchestrator
description: 여행 자동화 전체 파이프라인을 하네스(harness) 구조로 실행하는 오케스트레이터. trip-brief.json을 단일 입력으로 받아 리서치 → 노션 생성 → 이미지 → 지도 → 보강 → 검증 루프 → 산출물 단계를 상태 기반으로 진행하며, 각 단계는 게이트(gate)를 통과해야만 다음으로 넘어간다. 실패한 항목은 워크 큐에 남아 최대 3회까지 자동 재시도된다. 사용자가 여행 가이드 전체 생성, 여행 자동화 실행, /new-trip, 파이프라인 재개, 특정 단계만 다시 실행 등을 요청할 때 사용. travel-intake 스킬이 먼저 실행되어 trip-brief.json이 있어야 한다.
---

# Travel Orchestrator v3 — 하네스 & 루프 구조

## 설계 원칙

v2는 Phase 0 → Phase 6의 **일직선 파이프라인**이었다. 문제는 중간 단계가 부분 실패했을 때 감지되지 않고 그대로 다음 단계로 넘어갔다는 점이다.

v3는 세 가지를 바꿔다.

1. **상태 파일 기반 하네스** — 진행 상황이 파일에 남아 중단·재개가 가능하다
2. **게이트** — 각 단계는 검증을 통과해야만 완료 처리된다
3. **워크 큐 루프** — 실패 항목이 큐에 남아 자동 재시도된다

## 상태 파일

작업 디렉터리: `/tmp/{trip_slug}/`

| 파일 | 역할 |
|---|---|
| `trip-brief.json` | 입력 단일 진실 공급원. **오케스트레이터는 이 파일을 수정하지 않는다** |
| `state.json` | 단계별 상태, 생성된 페이지 ID, 재시도 카운터 |
| `work_queue.json` | 실패·미완 항목 큐 |
| `research/*.md` | 스팟별 리서치 결과 |
| `assets/` | KML·CSV·이미지·프롬프트 |
| `report.md` | 최종 완료 리포트 |

### state.json 스키마

```json
{
  "trip_slug": "yellowstone-2026",
  "stages": {
    "S1_research":    {"status": "done",    "attempts": 1, "gate": "pass"},
    "S2_scaffold":    {"status": "done",    "attempts": 1, "gate": "pass"},
    "S3_content":     {"status": "running", "attempts": 1, "gate": null},
    "S4_images":      {"status": "pending", "attempts": 0, "gate": null},
    "S5_illustration":{"status": "pending", "attempts": 0, "gate": null},
    "S6_maps":        {"status": "pending", "attempts": 0, "gate": null},
    "S7_enrich":      {"status": "pending", "attempts": 0, "gate": null},
    "S8_audit":       {"status": "pending", "attempts": 0, "gate": null},
    "S9_export":      {"status": "pending", "attempts": 0, "gate": null}
  },
  "notion": {
    "main_page_id": "...",
    "day_pages": {"1": "...", "2": "..."},
    "reference_pages": {"동물 도감": "..."}
  },
  "spots": [
    {"id": "old-faithful", "day": 2, "name_ko": "올드페이스풀",
     "lat": 44.4605, "lon": -110.8281,
     "images": 2, "has_tips": true, "has_parking": true, "has_besttime": true}
  ],
  "failures": []
}
```

`status` 값: `pending` → `running` → `done` / `failed`
`gate` 값: `null` → `pass` / `fail`

---

## 단계 정의

각 단계는 **실행 → 게이트 검증 → 상태 기록** 3부로 구성된다.

### S1. 리서치

- 스킬: `travel-research`, **`travel-naver-search`(필수)**, `travel-url-ingest`
- 실행: Agent tool로 3~4일치씨 묶어 병렬 처리
- **네이버 검색은 선택이 아니다.** 스팟마다 최소 1회 네이버 블로그/카페 검색을 수행한다.

**게이트 G1**: 모든 스팟에 대해 `research/{spot_id}.md` 존재, 6개 카테고리 섹션 모두 500자 이상, 네이버 출처 최소 1건

실패 시: 해당 스팟만 `work_queue`에 적재

### S2. 노션 스캐폴드

- 스킬: `notion-travel-page`
- 메인 페이지 + 날짜별 페이지 + 참고 자료 페이지의 **껵데기만** 먼저 만든다. 각 페이지 ID를 `state.json`에 즉시 기록

> ⚠️ 메인 페이지에 `replace_content` + `allow_deleting_content: true`를 쓰면 새 본문에서 참조되지 않은 하위 페이지가 **전부 아카이브된다.** 스캐폴드 이후 메인 페이지 수정은 반드시 `update_content` 또는 `insert_content`를 쓔다.

**게이트 G2**: 모든 페이지 ID가 확보되고, `fetch`로 각 페이지가 정상 조회됨

### S3. 본문 작성

- 스킬: `notion-travel-page`
- 날짜별 페이지에 타임라인 · 스팟별 상세 · 이동 시간표 작성

**게이트 G3 — 한글 무결성 검사 (필수)**: 작성 직후 각 페이지를 `fetch`로 되읽어 자모 분리·대체문자·이스케이프 잔재를 기계 탐지하고, **각 페이지를 실제로 읽어 어색한 단어를 직접 확인**한다. 기계 검사만으로는 "열로스톤", "통밥집" 같은 **의미는 파손되었지만 형태는 정상 한글인 오류**를 못 잡는다.

실패 시: 해당 페이지를 `replace_content`로 재작성 (한글 직접 입력)

### S4. 스톡 이미지

- 스킬: `travel-image-search` → `travel-image-validator`
- 정책: `policies.min_images_per_spot` (기본 2장), 소제목마다 별도 이미지

**게이트 G4**: 모든 스팟 최소 장수 충족, 모든 이미지 URL HTTP 200 (curl 검증)

### S5. AI 일러스트

- 스킬: `travel-illustration`
- 산출: 전체 여정 요약 1장 + 날짜별 N장

**게이트 G5**: 요약 1장 + 날짜별 전량이 노션 파일 업로드 ID를 갖고 페이지에 삽입됨

### S6. 지도 연동

- 스킬: `travel-maps-integration`

**게이트 G6**: 모든 날짜 페이지에 지도 섹션 존재, KML이 XML 파싱 통과, 좌표가 바운딩 박스 안에 있음

### S7. 콘텐츠 보강

- 스킬: `travel-content-enrichment`, `travel-spot-reviews`, `travel-packing-list`, `travel-emergency-info`, `travel-transport-info`

**게이트 G7**: 모든 스팟에 관람 포인트 · 역사 · 주차 · 추천 시간대 · 팁이 존재

### S7.5. 지출 관리 구축

- 스킬: `travel-expense-db`
- 확정 예약은 실제 금액·확인번호로, 나머지는 예상/미확정으로 채운다
- 반환된 data source ID를 `state.json`의 `expense_data_source_id`에 기록

여행 중·후에 `travel-receipt-ocr`이 이 데이터베이스에 영수증을 쌓는다.

### S8. 종합 감사 루프 ★

- 스킬: `travel-quality-loop`
- **여기서 통과할 때까지 S3~S7로 되돌아간다.** 최대 3회 순환.

### S9. 산출물 내보내기

- 스킬: `travel-calendar-sync`, `travel-presentation`, xlsx 스킬
- `report.md` 작성 후 사용자에게 파일 전달

---

## 워크 큐 루프

```
while work_queue 비어있지 않음 and 전체_순환 < 3:
    item = work_queue.pop()
    if item.attempts >= 3:
        failures.append(item)
        continue
    item.attempts += 1
    해당 단계 재실행(item)
    게이트 재검증
    if 통과: state 갱신
    else:    work_queue.push(item)
```

**3회 실패한 항목은 조용히 버리지 않는다.** `report.md`의 "수동 확인 필요" 절에 항목·사유·시도 이력을 남긴다.

---

## 치명적 규칙 (위반 시 전면 재작업)

1. **한글을 유니코드 이스케이프로 쓰지 않는다.** 항상 문자 그대로 입력한다
2. 노션 마크다운 이스케이프: `~`는 `\~`, `$`는 `\$`
3. **요일은 계산한다, 추론하지 않는다.** `trip-brief.json`의 `day_map`만 사용
4. `replace_content` + `allow_deleting_content: true` 는 하위 페이지를 아카이브한다. 메인 페이지에는 쓰지 않는다
5. AI 일러스트 ≠ 스톡 사진. 둘 다 만든다
6. 이미지 URL은 반드시 curl로 검증한다
7. 브라우저 자동화는 1순위가 아니다. 2회 실패하면 즉시 포기하고 대안으로 전환한다

---

## 부분 실행

| 사용자 신호 | 실행 |
|---|---|
| "리서치만" | S1 |
| "노션만 만들어줘" | S2~S3 |
| "사진 다시 넣어줘" | S4 |
| "그림 생성" | S5 |
| "지도 붙여줘" | S6 |
| "전체 점검해줘" | S8 |
| "비용 정리해줘" | S7.5 |
| "영수증 넣어줘" | `travel-receipt-ocr` (파이프라인 밖) |
| "이어서 해줘" | `state.json` 읽고 `pending`부터 재개 |
| "Day 5만 다시" | 해당 항목만 큐에 넣고 S3~S7 |

## 완료 리포트 형식

```markdown
## ✅ {여행명} 가이드 생성 완료

### 산출물
- 📄 노션 메인: {URL}
- 📝 날짜별 페이지 {N}개 · 참고 자료 {M}개
- 📍 스팟 {K}개
- 🖼️ 스톡 이미지 {N}개
- 🎨 AI 일러스트 {N}장
- 🗺️ KML / CSV / routes.md

### 게이트 통과 현황
| 단계 | 결과 | 재시도 |
|---|---|---|

### ⚠️ 수동 확인 필요
- (3회 실패 항목 · 사유 · 대안)

### 📌 적용한 가정
- (무인 실행 시 사용자 확인 없이 채택한 기본값)
```

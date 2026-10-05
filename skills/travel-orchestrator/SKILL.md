---
name: travel-orchestrator
description: 여행 자동화 전체 파이프라인을 하네스(harness) 구조로 실행하는 오케스트레이터. trip-brief.json을 단일 입력으로 받아 리서치 → 노션 생성 → 이미지 → 지도 → 보강 → 검증 루프 → 산출물 단계를 상태 기반으로 진행하며, 각 단계는 게이트(gate)를 통과해야만 다음으로 넘어간다. 실패한 항목은 워크 큐에 남아 최대 3회까지 자동 재시도된다. 사용자가 여행 가이드 전체 생성, 여행 자동화 실행, /new-trip, 파이프라인 재개, 특정 단계만 다시 실행 등을 요청할 때 사용. travel-intake 스킬이 먼저 실행되어 trip-brief.json이 있어야 한다.
---

# Travel Orchestrator v3 — 하네스 & 루프 구조

## 설계 원칙

v2는 Phase 0 → Phase 6의 **일직선 파이프라인**이었다. 문제는 중간 단계가 부분 실패했을 때 감지되지 않고 그대로 다음 단계로 넘어갔다는 점이다. 이미지가 안 붙은 페이지, 한글이 깨진 페이지, 지도가 빠진 페이지가 "완료"로 보고됐다.

v3는 세 가지를 바꾼다.

1. **상태 파일 기반 하네스** — 진행 상황이 파일에 남아 중단·재개가 가능하다
2. **게이트** — 각 단계는 검증을 통과해야만 완료 처리된다
3. **워크 큐 루프** — 실패 항목이 큐에 남아 자동 재시도된다

```
                    ┌──────────────────────────────┐
                    │   trip-brief.json (SSOT)     │
                    └──────────────┬───────────────┘
                                   │
   ┌───────────────────────────────▼────────────────────────────────┐
   │                        HARNESS LOOP                            │
   │                                                                │
   │   ┌─────────┐   ┌──────┐   ┌────────┐   ┌──────────────────┐   │
   │   │ 단계실행 │──▶│ 게이트 │──▶│ 통과?  │──▶│ state.json 갱신  │   │
   │   └─────────┘   └──────┘   └───┬────┘   └──────────────────┘   │
   │        ▲                       │ 실패                          │
   │        │                       ▼                               │
   │   ┌────┴─────────────┐   ┌──────────────┐                      │
   │   │  work_queue 소비  │◀──│ 실패 항목 적재 │  (최대 3회)          │
   │   └──────────────────┘   └──────────────┘                      │
   └────────────────────────────────────────────────────────────────┘
```

---

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
    "reference_pages": {"동물 도감": "...", "지질 이야기": "..."}
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

- 스킬: `travel-research`, **`travel-naver-search`(필수)**, `travel-url-ingest`(참고 URL 있을 때)
- 실행: Agent tool로 3\~4일치씩 묶어 병렬 처리
- **네이버 검색은 선택이 아니다.** 영문 웹만으로는 한국인 여행자 관점의 정보(현지 결제 방식, 한식 조달, 아이 동반 실제 후기, 시차 적응)가 누락된다. 스팟마다 최소 1회 네이버 블로그/카페 검색을 수행한다.

**게이트 G1**
- 모든 스팟에 대해 `research/{spot_id}.md` 존재
- 각 파일에 6개 카테고리 섹션이 모두 있고 각 500자 이상
- 네이버 출처가 최소 1건 포함
- 통계·요금·운영시간에 출처 URL 존재

실패 시: 해당 스팟만 `work_queue`에 적재

---

### S2. 노션 스캐폴드

- 스킬: `notion-travel-page`
- 메인 페이지 + 날짜별 페이지 + 참고 자료 페이지의 **껍데기만** 먼저 만든다
- 각 페이지 ID를 `state.json`에 즉시 기록

> ⚠️ **하위 페이지 아카이빙 사고 방지**
> 메인 페이지에 `replace_content` + `allow_deleting_content: true`를 쓰면 새 본문에서 참조되지 않은 하위 페이지가 **전부 아카이브된다.** 스캐폴드 이후 메인 페이지 수정은 반드시 `update_content` 또는 `insert_content`를 쓴다. 부득이 `replace_content`를 써야 하면 새 본문에 모든 하위 페이지의 `<page url=...>` 링크를 포함시킨다.

**게이트 G2**: 모든 페이지 ID가 확보되고, `fetch`로 각 페이지가 정상 조회됨

---

### S3. 본문 작성

- 스킬: `notion-travel-page`
- 날짜별 페이지에 타임라인 · 스팟별 상세 · 이동 시간표 작성
- **한글 인코딩 규칙 준수** (아래 "치명적 규칙" 참조)

**게이트 G3 — 한글 무결성 검사 (필수)**

작성 직후 각 페이지를 `fetch`로 되읽어 다음을 점검한다.

```python
# 자모 분리, 대체문자, 이스케이프 잔재 탐지
import re
BAD = [
    r'[ᄀ-ᇿ]',        # 조합용 자모 (정상 한글에는 없어야 함)
    r'[�]',               # 대체 문자
    r'\\u[0-9a-fA-F]{4}',      # 이스케이프 잔재
    r'[가-힣]{1,2}[�]',
]
```

기계 검사만으로는 "열로스톤", "통밥집", "밽난로" 같은 **의미는 파손됐지만 형태는 정상 한글인 오류**를 못 잡는다. 따라서 **각 페이지를 실제로 읽어 어색한 단어를 직접 확인**한다. 고유명사(지명·시설명)를 원문 표기와 대조하는 것이 가장 효과적이다.

실패 시: 해당 페이지를 `replace_content`로 재작성 (한글 직접 입력)

---

### S4. 스톡 이미지

- 스킬: `travel-image-search` → `travel-image-validator`
- 정책: `policies.min_images_per_spot` (기본 2장), 소제목마다 별도 이미지
- 폭 `policies.image_width_px` (기본 1280px)

**게이트 G4**
- 모든 스팟이 최소 장수 충족
- 모든 이미지 URL이 HTTP 200 (curl 검증)

```bash
curl -s -o /dev/null -w "%{http_code}" -L --max-time 20 "$URL"
```

실패 시: 해당 스팟을 `work_queue`에 적재, 다른 키워드로 재검색

---

### S5. AI 일러스트

- 스킬: `travel-illustration`
- 산출: 전체 여정 요약 1장 + 날짜별 N장
- 노션 업로드 후 각 페이지 상단 배치

**게이트 G5**: 요약 1장 + 날짜별 전량이 노션 파일 업로드 ID를 갖고 페이지에 삽입됨

---

### S6. 지도 연동

- 스킬: `travel-maps-integration`
- 산출: 날짜별 임베드 지도 + 모바일 내비 딥링크 + 스팟별 좌표 링크 표 + KML/CSV/routes.md + 전체 지도 페이지

**게이트 G6**
- 모든 날짜 페이지에 `## 🗺️ Day N 지도` 섹션 존재
- KML이 XML 파싱 통과
- 좌표가 여행 지역 바운딩 박스 안에 있음 (오타 검출)

---

### S7. 콘텐츠 보강

- 스킬: `travel-content-enrichment`, `travel-spot-reviews`, `travel-packing-list`, `travel-emergency-info`, `travel-transport-info`

**게이트 G7**: 모든 스팟에 관람 포인트 · 역사 · 주차 · 추천 시간대 · 팁이 존재

---

### S7.5. 지출 관리 구축

- 스킬: `travel-expense-db`
- **💵 지출 관리 데이터베이스**와 **🧾 경비 총괄 페이지**를 만든다
- 확정 예약은 실제 금액·확인번호로, 나머지는 예상/미확정으로 채운다
- 반환된 data source ID를 `state.json`의 `expense_data_source_id`에 기록한다
- 게이트: 분류별 소계 합 = 총액, 비중 합 = 100%, 환불성 보증금이 총액에서 제외됐는지

여행 중·후에 `travel-receipt-ocr`이 이 데이터베이스에 영수증을 쌓는다. 파이프라인 밖에서 `/trip-receipt`로 단독 실행된다.

---

### S8. 종합 감사 루프 ★

- 스킬: `travel-quality-loop`
- **여기서 통과할 때까지 S3\~S7로 되돌아간다.** 최대 3회 순환.

---

### S9. 산출물 내보내기

- 스킬: `travel-calendar-sync`, `travel-presentation`, xlsx 스킬
- `report.md` 작성 후 사용자에게 파일 전달

---

## 워크 큐 루프

```
while work_queue 비어있지 않음 and 전체_순환 < 3:
    item = work_queue.pop()
    if item.attempts >= 3:
        failures.append(item)      # 포기하고 리포트에 기록
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

### 1. 한글을 유니코드 이스케이프로 쓰지 않는다

노션 MCP에 콘텐츠를 넘길 때 `옵로...` 같은 형태로 조립하면 **한글이 파손된다.** 실제로 11개 페이지 전체가 파손된 사례가 있다 (옐로스톤→"열로스톤", 통나무집→"통밥집", 진흙온천→"진흥온천").

**한글은 항상 문자 그대로 입력한다.**

### 2. 노션 마크다운 이스케이프

| 문자 | 표기 | 이유 |
|---|---|---|
| `~` | `\~` | 취소선으로 해석됨 |
| `$` | `\$` | 수식으로 해석됨 |

### 3. 요일은 계산한다, 추론하지 않는다

`trip-brief.json`의 `day_map`만 사용한다. 페이지 제목·표·타임라인의 모든 요일 표기가 이 매핑과 일치하는지 S8에서 재검증한다.

### 4. `replace_content` + `allow_deleting_content: true` 는 하위 페이지를 아카이브한다

메인 페이지에는 쓰지 않는다. 이미 아카이브됐다면 `notion-move-pages`로는 복구되지 않으며, 사용자가 노션 휴지통에서 직접 복원해야 한다.

### 5. AI 일러스트 ≠ 스톡 사진

용도가 다르다. 둘 다 만든다.

### 6. 이미지 URL은 반드시 curl로 검증한다

Pexels 사진 ID는 삭제될 수 있다. 검색 결과에 나온 ID라도 404가 뜬다.

### 7. 브라우저 자동화는 1순위가 아니다

예약 사이트·구글맵에 대한 브라우저 자동화는 봇 차단과 스크립트 주입 타임아웃으로 반복 실패한다. **공식 URL·전화번호·API·파일 생성(KML/CSV)** 을 우선하고, 브라우저는 2회 실패하면 즉시 포기하고 대안으로 전환한다.

---

## 부분 실행

| 사용자 신호 | 실행 |
|---|---|
| "리서치만" | S1 |
| "노션만 만들어줘" | S2\~S3 |
| "사진 다시 넣어줘" | S4 |
| "그림 생성" | S5 |
| "지도 붙여줘" | S6 |
| "전체 점검해줘" | S8 |
| "비용 정리해줘" | S7.5 |
| "영수증 넣어줘" | `travel-receipt-ocr` (파이프라인 밖) |
| "이어서 해줘" | `state.json` 읽고 `pending`부터 재개 |
| "Day 5만 다시" | 해당 항목만 큐에 넣고 S3\~S7 |

## 완료 리포트 형식

```markdown
## ✅ {여행명} 가이드 생성 완료

### 산출물
- 📄 노션 메인: {URL}
- 📝 날짜별 페이지 {N}개 · 참고 자료 {M}개
- 📍 스팟 {K}개 (전부 사진 {min}장 이상 · 좌표 링크 포함)
- 🖼️ 스톡 이미지 {N}개 (검증 {정상}/{교체})
- 🎨 AI 일러스트 {N}장 (전체 1 + 날짜별 {N-1})
- 🗺️ KML / CSV / routes.md

### 게이트 통과 현황
| 단계 | 결과 | 재시도 |
|---|---|---|

### ⚠️ 수동 확인 필요
- (3회 실패 항목 · 사유 · 대안)

### 📌 적용한 가정
- (무인 실행 시 사용자 확인 없이 채택한 기본값)
```

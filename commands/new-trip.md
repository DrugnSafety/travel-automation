---
description: 여행 일정표로 전체 가이드 자동 생성 (하네스 + 품질 루프)
argument-hint: "<여행 일정 설명 또는 파일>"
---

사용자가 여행 자동화를 요청했다. **travel-orchestrator 하네스**로 실행하라.

## 0단계: 인테이크 (건너뛰지 말 것)

**`travel-intake` 스킬을 먼저 실행한다.** 이 단계를 건너뛰면 뒤에서 반드시 재작업이 생긴다.

`travel-intake`는 6개 블록의 질문을 AskUserQuestion으로 최대 3회에 나눠 묻고, 다음을 확정한다.

- 일정·기간·출발지·인원 (고령자 동반 여부 별도 확인)
- **요일 매핑을 직접 계산해 사용자에게 확인받는다** (추론 금지)
- 구간별 교통수단과 차량 정확한 규격(ft)
- **차량 통행 제약을 직접 조사**해 일정에 반영 (터널 폭·높이, 차량 길이 제한)
- 숙박의 **공원 내/외 구분**과 예약처(운영사가 갈릴 수 있음)
- 지도 연동 범위 + **구글맵 개인 저장 목록에는 API 쓰기가 불가능하다는 사실을 미리 고지**
- 스팟당 최소 이미지 수(기본 2장), AI 일러스트 생성 여부
- 아동 교육용 참고 페이지 생성 여부
- 산출물과 노션 부모 페이지

`$ARGUMENTS`에 이미 담긴 정보는 묻지 않는다. 무인 실행이면 기본값을 적용하고 채택한 가정을 리포트에 명시한다.

결과물: **`/tmp/{trip_slug}/trip-brief.json`** — 이후 모든 단계가 이 파일만 읽는다.

## 1단계: 하네스 실행

`travel-orchestrator` 스킬의 S1~S9를 상태 기반으로 진행한다. 각 단계는 게이트를 통과해야 완료 처리한다.

| 단계 | 스킬 | 게이트 |
|---|---|---|
| S1 리서치 | `travel-research` + **`travel-naver-search`(필수)** + `travel-url-ingest` | 스팟별 6개 카테고리 + 네이버 출처 1건 이상 |
| S2 스캐폴드 | `notion-travel-page` | 페이지 ID 확보 및 조회 성공 |
| S3 본문 | `notion-travel-page` | **한글 무결성 검사 통과** |
| S4 사진 | `travel-image-search` → `travel-image-validator` | 스팟당 최소 장수 + 전 URL 200 |
| S5 일러스트 | `travel-illustration` | 전체 1장 + 날짜별 전량 삽입 |
| S6 지도 | `travel-maps-integration` | 전 날짜 지도 섹션 + KML 파싱 + 좌표 검증 |
| S7 보강 | `travel-content-enrichment`, `travel-spot-reviews`, `travel-packing-list`, `travel-emergency-info`, `travel-transport-info` | 스팟별 5개 블록 완비 |
| S8 감사 | **`travel-quality-loop`** | 12개 체크 통과 (최대 3회 순환) |
| S9 산출 | `travel-calendar-sync`, `travel-presentation`, xlsx | 파일 전달 완료 |

정보 소스 선택이 애매하면 `travel-external-sources`를 참조한다.

## 2단계: 워크 큐

게이트 실패 항목은 `work_queue.json`에 적재해 자동 재시도한다. **3회 실패한 항목은 조용히 버리지 말고** 리포트의 "수동 확인 필요"에 사유와 시도 이력을 남긴다.

## 3단계: 완료 리포트

`travel-orchestrator`의 리포트 형식을 따른다. 게이트 통과 현황 표, 수동 확인 필요 항목, 적용한 가정을 반드시 포함한다.

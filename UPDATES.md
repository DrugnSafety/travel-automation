# 업데이트 내역

간단한 요약은 [README.md](README.md)에도 있습니다. 여기에는 버전별 상세 변경 사항을 기록합니다.

## v3.2.1 — 2026-10-05

**GitHub 공개본을 실제 사용 중인 최종본과 일치시켰습니다.** v3.2.0 동기화 때 일부 파일이 빠지고, 유니코드 이스케이프 수기 입력으로 한글이 깨진 채 올라간 문제를 바로잡은 릴리스입니다. 이제 README가 안내하는 스킬 21개·명령어 8개가 저장소에 모두 들어 있습니다.

- **누락분 반영**
  - 스킬 3종: `travel-quality-loop`, `travel-receipt-ocr`, `travel-url-ingest`
  - 스크립트 2종: `travel-maps-integration/scripts/build_map_assets.py`, `travel-receipt-ocr/scripts/receipt_intake.py`
- **최종본으로 교체한 파일 13개** — 깨진 한글 교정(예: 옥로스톤 → 옐로스톤, 진흘온첨 → 진흙온천, 캐션 → 캡션, "표 셀은 좋다" → "표 셀은 좁다"), 축약돼 있던 `travel-orchestrator`를 전문으로 복원, 그 밖의 표기 차이 정리
- **폐지 스텁 4종 삭제** — `travel-image-generator`, `travel-notion-export`, `travel-plan-intake`, `travel-study-guide`. 이름 변경 매핑은 아래 v3.2.0 표에 남겨 둡니다
- **`.mcp.json` 수정** — `claude plugin validate` 오류 9건으로 모든 번들 서버가 로드 시 조용히 제외되던 문제를 해결
  - `kiwi-flights`, `trivago-hotels`: 공식 문서 기준 `http` 전송 방식으로 수정해 정상 로드
  - `lilt-translation`(기업 계정 OAuth 필요), `google-maps`(Composio 계정별 URL·API 키 필요) 제거 — 직접 연결 방법은 README와 `travel-spot-reviews`에 안내
  - 서버가 아닌 `_recommended` 항목 제거 — 권장 커넥터 목록은 README로 이동
- **스킬 문서 오기 2건 수정** — `travel-orchestrator`의 이스케이프 예시가 일반 한글(`옵로...`)로 바뀌어 있던 것을 `\uc610\ub85c...` 형태로 복원, `/trip-receipt`의 "6단계를 건너뛰면"을 실제 단계 번호인 7단계(대사)로 정정
- **예시 데이터 일반화** — `travel-intake`의 trip-brief 예시(이름·Notion 페이지 ID)와 `receipt_intake.py` 예시(카드 뒷자리)를 일반 예시값으로 교체
- **문서**
  - README 전면 개편: Claude 앱·Claude Code 설치 방법, 사전 준비(필수·권장·선택), 단계별 게이트, 알려진 제약, 영문 요약
  - 실제 동작과 다르던 설명 정정: 사진 소스(Wikipedia → Pexels 우선), 일러스트 API 키 경로(`~/.config/gpt-image/.env`), 캘린더 ICS 폴백 문구 삭제, 번들 커넥터 목록
  - `.gitignore` 추가

## v3.2.0 — 2026-08-18

**GitHub 저장소를 실제 사용 중인 최신 구조와 동기화하고, 문서를 정비했습니다.**

이전까지 GitHub에는 2026-07-07 최초 커밋 이후 갱신이 없었지만, 실제로는 그사이 플러그인이 상당히 재작성되어 있었습니다. 이번 릴리스는 그 간극을 해소합니다.

- **문서**
  - README에 설치 가이드 신설 (`.claude-plugin/marketplace.json` 추가 → `/plugin marketplace add` + `/plugin install`로 설치 가능)
  - 상세 변경 이력을 이 파일(`UPDATES.md`)로 분리, README는 요약만 유지
  - `plugin.json`에 `homepage`/`repository` 필드 추가
- **스킬 동기화** — 아래 [스킬 이름 변경/폐지 매핑](#스킬-이름-변경폐지-매핑) 참고
  - 신규 8종: `travel-intake`, `travel-quality-loop`, `travel-illustration`, `travel-naver-search`, `travel-url-ingest`, `travel-external-sources`, `travel-expense-db`, `travel-receipt-ocr` (일부는 v3.1 시점에 이미 로컬에 존재했으나 GitHub에는 반영되지 않았던 항목 포함)
  - 이름 변경 2종: `travel-plan-intake` → `travel-intake`, `travel-image-generator` → `travel-illustration`
  - 폐지 2종: `travel-notion-export`(GitHub 백업 기능, 제외됨), `travel-study-guide`(전용 예습 자료 생성, 제외됨 — 일부 기능은 `travel-content-enrichment`에 포함)
  - 명령어 5종 추가: `/trip-audit`, `/trip-expense`, `/trip-images`, `/trip-map`, `/trip-receipt`
- **버전 표기 정정** — GitHub에 공개된 `plugin.json`이 실제로는 서로 다른 두 구조(구 아키텍처와 상태 하네스 재작성판)에 대해 동일하게 `3.1.0`을 표기하고 있었습니다. 이번에 `3.2.0`으로 올려 향후 업데이트 감지가 정상 동작하도록 정정했습니다.

> 참고: 이름 변경/폐지된 4개 스킬 폴더는 GitHub API 제약으로 완전히 삭제하지 못하고, 대신 각 `SKILL.md`를 안내 문구로 교체했습니다. 완전히 지우려면 저장소에서 해당 폴더를 수동으로 삭제하세요. → **v3.2.1에서 삭제 완료.** 또한 이 릴리스의 실제 저장소에는 `travel-quality-loop`, `travel-receipt-ocr`, `travel-url-ingest`가 빠져 있었으며 v3.2.1에서 반영했습니다.

### 스킬 이름 변경/폐지 매핑

| 이전 이름 | 현재 상태 |
|---|---|
| `travel-plan-intake` | → `travel-intake`로 이름 변경 + 기능 확장 |
| `travel-image-generator` | → `travel-illustration`로 이름 변경 + 기능 확장 |
| `travel-notion-export` | 폐지 (GitHub 백업 기능 제외) |
| `travel-study-guide` | 폐지 (일부 기능은 `travel-content-enrichment`에 포함) |

## v3.1.0 아키텍처 재작성 — 날짜 미상 (로컬 플러그인 캐시 기준, GitHub 미반영 상태로 진행됨)

v2의 일직선 파이프라인(Phase 0 → Phase 6)을 상태 기반 하네스로 전면 재작성했습니다. 중간 단계가 부분 실패해도 감지되지 않고 다음으로 넘어가, 이미지가 없는 페이지나 한글이 깨진 페이지가 "완료"로 보고되는 문제를 해결하기 위한 재작업입니다.

- **상태 기반 하네스** — `state.json`에 단계별 진행 상황을 남겨 중단·재개 가능
- **게이트** — 각 단계는 검증을 통과해야만 완료 처리. 실패 항목은 워크 큐에 남아 최대 3회 자동 재시도, 그래도 실패하면 리포트의 "수동 확인 필요"에 기록
- **인테이크 선행** — 재작업을 유발하던 전제 조건(요일 계산, 차량 통행 제약, 공원 내외 숙소 구분, 이미지 밀도, 지도 연동 범위 등)을 시작 전에 전부 확정
- 신규: `travel-intake`, `travel-quality-loop`, `travel-maps-integration`, `travel-illustration`, `travel-naver-search`, `travel-url-ingest`, `travel-external-sources`
- v3.1 추가: `travel-expense-db`(지출 관리 DB + 경비 총괄 페이지), `travel-receipt-ocr`(영수증 사진·PDF → 지출 DB 자동 등록)

## v3.1.0 최초 공개판 — 2026-07-07 (GitHub 최초 커밋)

GitHub에 처음 공개된 버전. 17개 스킬 + 3개 슬래시 커맨드로 구성.

핵심 변경 (v2 → v3.0):

| 문제 (v2) | 해결 (v3.0) |
|---|---|
| 노션 이미지가 자꾸 깨짐 | Wikipedia/Commons 직링크 API + `notion-create-attachment` 첨부 업로드로 Notion 호스팅 |
| 관련 없는 이미지 삽입 | 삽입 전 모든 이미지를 다운로드해 Read로 직접 열어 시각 검증 |
| 사용자 계획/파일 활용 미흡 | `travel-plan-intake` 신설 — 파일·텍스트·지도 리스트 URL 파싱, 없으면 대화형 인터뷰 |
| Google Maps 연계 부족 | `travel-maps-integration` 신설 — 스팟 딥링크·Day 경로 링크·이동시간 검증·지도 리스트 임포트 |
| 예습용 스팟 상세 부족 | `travel-study-guide` 신설 — 아이 코너 + 부모 브리핑 |
| AI 이미지 스타일 없음 | `travel-image-generator` 신설 — 19종 스타일 라이브러리 |

v3.1에서 `travel-notion-export`(Notion 가이드북 → 마크다운 → GitHub 백업) 추가.

이 구조는 이후 상태 하네스 기반으로 재작성되었으며(위 "v3.1.0 아키텍처 재작성" 항목), 이름 변경·폐지 매핑은 v3.2.0 항목의 표에 정리했습니다.

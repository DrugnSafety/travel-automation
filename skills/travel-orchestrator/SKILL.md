---
name: travel-orchestrator
description: 여행 계획 입력(또는 대화형 창조)부터 Notion 가이드북, 이미지, 구글맵 연계, 가족 예습 자료, Google Calendar, PPT까지 전체 여행 가이드 제작 파이프라인을 자동 오케스트레이션합니다. 사용자가 여행 자동화, 여행 가이드 만들기, 전체 여행 세팅, 여행 패키지 실행, 여행 파이프라인 등을 요청할 때 이 스킬을 사용하세요.
---

# Travel Orchestrator v3

여행 계획 하나로 완성도 높은 가이드(Notion + Maps + 예습자료 + Calendar + PPT)를 자동 생성한다. 모든 단계는 **표준 스냅샷 JSON**을 통해 데이터를 주고받는다.

## 파이프라인 (12단계)

```
Phase 0   travel-plan-intake        — 사용자 자료 파싱 or 대화형 계획 창조 → plan.json
Phase 0.3 스타일 질문 (AskUserQuestion 1회) — 히어로 이미지 스타일 + 산출물 범위 확인
Phase 0.5 travel-transport-info     — 예약 자료 schema.org 파싱 → transport.json
Phase 1   travel-research           — 스팟별 6카테고리 리서치 (Agent 병렬) → enriched.md
Phase 2   notion-travel-page        — 메인 + Day별 + 유틸 서브 페이지 생성 → notion_ids.json
Phase 2.5 travel-maps-integration   — 지도 딥링크·경로·이동시간 검증·날씨 → maps.json
Phase 3   travel-image-search       — 실사 이미지 확보 + 시각 검증 + 첨부 업로드 → images.json
Phase 3.3 travel-image-generator    — (스타일 선택 시) 히어로·일정표·체크리스트 생성 이미지
Phase 3.5 travel-image-validator    — 접근성 + 관련성 2중 검증 & 교체
Phase 4   travel-content-enrichment — 6가지 상세 블록 보강
Phase 4.5 travel-spot-reviews       — Google Maps/커뮤니티 리뷰 팁·주의사항
Phase 4.7 travel-study-guide        — 🎓 서현이 코너 + 👩 부모 브리핑 페이지
Phase 5   travel-calendar-sync      — 캘린더 등록 (확인 후) / ICS 폴백
Phase 6   travel-presentation       — PPT 생성
Phase 7   완료 리포트 + 스냅샷 갱신 + 메모리 저장
```

## 표준 스냅샷: `/tmp/{여행지}_summary.json` (TREK get_trip_summary 패턴)

각 Phase 완료 시 이 파일에 결과를 병합한다. 이후 단계·재실행·부분 실행이 항상 이 파일 하나만 읽으면 되도록:

```json
{
  "plan": { ...plan.json 내용... },
  "transport": { ... }, "notion_ids": { ... }, "maps": { ... },
  "images": [ ... ], "enrichment_done": ["day1", ...],
  "calendar": {"events": 24, "method": "mcp|ics"},
  "ppt": {"file": "...", "slides": 18},
  "phase_log": [{"phase": "2", "status": "done", "at": "..."}]
}
```

- **부분 실행/재실행**: phase_log를 보고 완료된 단계는 건너뛴다 (중복 페이지·중복 이벤트 방지)
- 스냅샷이 이미 존재하는 여행이면 "이어서 진행할까요?" 확인

## Phase 0.3: 사용자 질문은 시작 시 한 번에 (중간 블로킹 금지)

AskUserQuestion 1회로 묶어서 질문:
1. **히어로 이미지 스타일**: 실사(기본) / 시네마틱 AI / 수채화 AI / 인포그래픽 AI (travel-image-generator 라이브러리 기준)
2. **산출물 범위**: 전체 / Notion만 / Notion+캘린더 (기본: 전체)
3. **예습 자료 포함 여부**: 서현이 코너 + 부모 브리핑 (기본: 포함)

이후 파이프라인은 캘린더 등록 확인(Phase 5)과 계획 창조 승인(Phase 0, 모드 B일 때) 외에는 질문 없이 완주한다.

## 단계별 핵심 규칙

| Phase | 규칙 |
|-------|------|
| 0 | plan.json의 스팟마다 `gmaps_query`·`wiki_title` 필수 채움 |
| 0.5 | 파싱 결과 pending → 사용자 확인 후 확정 |
| 1 | Day 3~4개 단위 Agent 병렬. 각 Agent에 6카테고리+출처 명시 지시 |
| 2 | 이미지 없는 상태로 골격 생성 (플레이스홀더 금지). MCP 리소스 enhanced-markdown-spec 선확인 |
| 2.5 | 이동시간 검증 결과가 plan과 20%+ 차이 시 경고 |
| 3 | 스팟당 위키피디아 1순위 → **Read로 시각 검증** → notion-create-attachment 업로드 |
| 3.5 | file-upload 첨부는 접근성 검사 스킵, 외부 embed만 HTTP 검사. 관련성은 전수 |
| 4.7 | 스팟당 아이용 800자+/부모용 500자+ |
| 5 | 이벤트 목록 테이블 확인 후 등록. MCP 실패 시 ICS 생성 |
| 6 | images.json의 로컬 사본 재활용 (재다운로드 금지) |

## 오류 처리

| 실패 단계 | 대응 |
|-----------|------|
| Phase 0 파싱 실패 | 원문 일부를 보여주고 수동 확인 요청 |
| Phase 1 리서치 | 실패 스팟만 재시도 3회 → 기본 정보로 진행, 리포트에 표기 |
| Phase 2 Notion API | 재시도 → replace_content 폴백. 실패 페이지는 스냅샷에 기록 후 계속 |
| Phase 3 이미지 | 소스 사다리 폴백 (wiki→commons→공식→생성) → 최종 실패 시 이미지 생략 |
| Phase 5 캘린더 | ICS 폴백 |
| Phase 6 PPT | PowerPoint MCP → pptx 라이브러리 폴백 |

어떤 단계도 전체 파이프라인을 중단시키지 않는다 — 실패는 기록하고 계속, 완료 리포트에 "수동 확인 필요" 섹션으로 정리.

## 부분 실행 라우팅

```
"계획만 정리해줘"       → Phase 0
"리서치만"             → Phase 1
"노션만 만들어줘"       → Phase 0(스냅샷 확인) + 2
"지도 연동해줘"         → Phase 2.5
"이미지만 넣어줘"       → Phase 3 + 3.5
"예습 자료 만들어줘"    → Phase 4.7
"캘린더만"             → Phase 5
"PPT만"                → Phase 6
```

## 완료 리포트 (두괄식 한국어)

```markdown
## ✅ {여행명} 가이드 생성 완료
- 📄 Notion: [메인 페이지]({URL}) + 서브 {N}개 (Day {N} · 예습 2 · 유틸 {N})
- 🖼️ 이미지: {N}장 (전량 시각 검증, 첨부 업로드 {N} / embed {N})
- 🗺️ 지도: 스팟 링크 {N}개 + Day 경로 {N}개, 이동시간 검증 {N}건
- 📅 캘린더: {N}개 이벤트 ({방식})
- 📊 PPT: {파일명} ({N}장)
### 수동 확인 필요
- {항목}
```

리포트 후: 메모리(`user_travel_*`) 갱신 + 산출물 파일은 present_files/SendUserFile로 전달.

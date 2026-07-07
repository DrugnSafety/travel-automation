---
description: 여행 계획(자료 유무 무관)으로 전체 가이드 자동 생성
argument-hint: "<여행 일정 설명, 파일 경로, 또는 지도 리스트 URL — 없어도 됨>"
---

사용자가 여행 전체 자동화를 요청했다. travel-orchestrator v3 파이프라인을 실행하라.

## 1단계: travel-plan-intake (필수 진입점)

`$ARGUMENTS`를 먼저 분류한다:
- 파일 경로/첨부 → 파싱 (텍스트·PDF·이미지·DOCX)
- 구글맵/네이버지도 저장 리스트 URL → travel-maps-integration 임포트로 스팟 추출
- 구체적 일정 텍스트 → 직접 파싱
- 막연한 요청 또는 빈 인자 → 대화형 인터뷰(AskUserQuestion 최대 2라운드) 후 Claude가 계획 창조 → 사용자 승인

결과: `/tmp/{여행지}_plan.json` (스팟별 gmaps_query·wiki_title 포함)

## 2단계: 시작 질문 1회 (AskUserQuestion)

- 히어로 이미지 스타일 (실사 / 시네마틱 AI / 수채화 AI / 인포그래픽 AI)
- 산출물 범위 (전체 / Notion만 / Notion+캘린더)
- 예습 자료(서현이 코너 + 부모 브리핑) 포함 여부 — 기본 포함

## 3단계: 파이프라인 실행

travel-orchestrator 스킬의 Phase 0.5~7을 순서대로 실행:

1. **travel-transport-info** — 예약 자료 schema.org 파싱 (자료 있을 때)
2. **travel-research** — 스팟별 6카테고리 리서치 (Agent 병렬)
3. **notion-travel-page** — 허브 아래 메인+Day+유틸 페이지 (사용자 노션 템플릿 구조)
4. **travel-maps-integration** — 스팟 지도 링크·Day 경로 링크·이동시간 검증·날씨
5. **travel-image-search** — 위키피디아 1순위 실사 + 시각 검증 + Notion 첨부 업로드
6. **travel-image-generator** — (AI 스타일 선택 시) 히어로·일정표·체크리스트 이미지
7. **travel-image-validator** — 접근성+관련성 2중 검증
8. **travel-content-enrichment** — 6가지 상세 블록
9. **travel-spot-reviews** — 리뷰 기반 팁·주의사항
10. **travel-study-guide** — 🎓 서현이 코너 + 👩 부모 브리핑
11. **travel-calendar-sync** — 이벤트 확인 후 등록 (실패 시 ICS 폴백)
12. **travel-presentation** — PPT

각 단계 완료 시 `/tmp/{여행지}_summary.json` 스냅샷 갱신. 실패 단계는 기록 후 계속 진행.

## 4단계: 완료 리포트

두괄식 한국어로 Notion URL·서브 페이지 수·이미지 검증 결과·캘린더 등록 수·PPT 파일을 요약하고, 산출 파일은 present_files로 전달. 메모리(`user_travel_*`) 갱신.

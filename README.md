# Travel Automation Plugin v3.1

여행 계획 하나(자료가 없으면 대화로)로 **Notion 가이드북 + 구글맵 연계 + 가족 예습 자료 + Google Calendar + PowerPoint**를 자동 생성하는 풀 패키지 여행 자동화 플러그인.

## v3.0 핵심 변경 — 문제 해결 중심

| 문제 (v2) | 해결 (v3) |
|-----------|-----------|
| 노션 이미지가 자꾸 깨짐 | ① Pexels ID 추측 조립 폐지 ② Wikipedia/Commons **직링크 API** 사용 ③ `notion-create-attachment` **첨부 업로드**로 Notion 호스팅 (외부 서버 무관) |
| 관련 없는 이미지 삽입 | 삽입 전 **모든 이미지를 다운로드해 Read로 직접 열어 시각 검증** (그 장소가 맞는지 확인) + validator에 관련성 검증 추가 |
| 사용자 계획/파일 활용 미흡 | 신규 `travel-plan-intake` — 파일·텍스트·지도 리스트 URL 파싱, 없으면 대화형 인터뷰 후 계획 창조 |
| Google Maps 연계 부족 | 신규 `travel-maps-integration` — 스팟 딥링크·Day 경로 링크·이동시간 검증·네이버/구글맵 리스트 임포트·날씨 |
| 예습용 스팟 상세 부족 | 신규 `travel-study-guide` — 🎓 아이 코너(스토리텔링·퀴즈·Junior Ranger) + 👩 부모 브리핑 (스팟당 800자+) |
| AI 이미지 스타일 없음 | 신규 `travel-image-generator` — 노션 프롬프트 DB 기반 **19종 스타일 라이브러리**, 사용자에게 스타일 질문 후 생성 |

## 스킬 (17개)

| # | 스킬 | 설명 | v3 |
|---|------|------|----|
| 1 | travel-plan-intake | 계획 파싱/대화형 창조 → 표준 plan JSON | 🆕 |
| 2 | travel-transport-info | 예약 자료 schema.org 파싱 | ⬆️ |
| 3 | travel-research | 스팟별 6카테고리 리서치 | |
| 4 | notion-travel-page | 사용자 노션 템플릿 구조로 3계층 페이지 생성 | ⬆️ |
| 5 | travel-maps-integration | 구글맵 딥링크·경로·리스트 임포트·날씨 | 🆕 |
| 6 | travel-image-search | 위키피디아 1순위 + 시각 검증 + 첨부 업로드 | ⬆️ |
| 7 | travel-image-generator | gpt-image-2 직접 생성 (19종 스타일 + 노션 프롬프트 22행 카탈로그) | 🆕 |
| 8 | travel-image-validator | 접근성 + 관련성 2중 검증 | ⬆️ |
| 9 | travel-content-enrichment | 6가지 상세 블록 보강 | |
| 10 | travel-spot-reviews | 리뷰 기반 팁·주의사항 | |
| 11 | travel-study-guide | 가족 예습 가이드 (아이+부모) | 🆕 |
| 12 | travel-calendar-sync | 캘린더 등록 + 지도 링크 + ICS 폴백 | ⬆️ |
| 13 | travel-presentation | PPT 생성 (Codex 기획 프롬프트 연동) | ⬆️ |
| 14 | travel-packing-list | 짐 싸기 체크리스트 | |
| 15 | travel-emergency-info | 긴급 정보 카드 | |
| 16 | travel-notion-export | 노션 가이드북(메인+서브페이지)을 마크다운 변환 후 GitHub push/commit | 🆕 v3.1 |
| 17 | travel-orchestrator | 12단계 파이프라인 + 스냅샷 JSON | ⬆️ |

## 슬래시 커맨드
- `/new-trip` — 전체 파이프라인 (자료 없이도 시작 가능)
- `/trip-checklist` — 짐 싸기 체크리스트
- `/trip-budget` — 여행 예산

## 파이프라인 (v3)

```
Intake → 스타일질문 → Transport → Research → Notion → Maps →
Images(실사) → [Images(AI)] → Validate → Enrich → Reviews →
StudyGuide → Calendar → PPT → 리포트
```

모든 단계는 `/tmp/{여행지}_summary.json` 스냅샷으로 연결 — 부분 실행·재실행 시 완료 단계 자동 스킵.

## GitHub 백업 (v3.1)

`travel-notion-export`로 완성된 노션 가이드북을 마크다운으로 변환해 GitHub에 백업할 수 있다. **플러그인 코드(이 리포)는 public, 여행 데이터(가족·자녀 정보 포함)는 반드시 별도 private 리포**로 분리한다 — 자세한 원칙은 스킬 문서 참조.

## 외부 연동

- **MCP**: Notion(필수), Google Calendar, Kiwi, Trivago, LILT, Google Maps(선택)
- **무키 API** (curl 직접 호출): Wikipedia REST, Wikimedia Commons, Open-Meteo(날씨), Nominatim/Overpass(OSM), 네이버지도 북마크 공유, Google Maps Universal URL
- **이미지 생성**: OpenAI `gpt-image-2` — API 키는 `~/.config/travel-automation/openai.env` (플러그인 파일에 키 미포함)
- **참고 레퍼런스**: mauriceboe/TREK (지도 리스트 임포트·schema.org 파싱·스냅샷 패턴 차용), 사용자 노션 여행 템플릿 + 이미지 프롬프트 DB

## 이미지 철칙 (v3)

> **단 한 장도 눈으로 확인하지 않은 이미지를 Notion에 넣지 않는다.**
> 다운로드 → Read로 시각 검증 → 첨부 업로드 → 삽입 → 재검증.

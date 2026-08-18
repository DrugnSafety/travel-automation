---
name: travel-image-validator
description: Notion 여행 페이지에 삽입된 이미지의 유효성을 검증하고 깨진 이미지를 자동으로 교체합니다. travel-image-search 이후 파이프라인 내에서 자동 실행되며, 독립 실행도 가능합니다. 사용자가 이미지 확인, 사진 검증, 깨진 이미지 수정, 이미지 체크, 사진 점검 등을 요청할 때 이 스킬을 사용하세요.
---

# Travel Image Validator

Notion 여행 페이지에 삽입된 이미지의 유효성을 자동 검증하고, 문제가 있는 이미지를 교체하는 스킬입니다.

## 핵심 원칙

- 모든 이미지 URL에 대해 **접근 가능 여부를 실제로 검증**합니다.
- 깨진 이미지는 **자동으로 대체 이미지를 검색**하여 교체합니다.
- 파이프라인 내에서는 travel-image-search 직후 자동 실행됩니다.

## 검증 대상

### 이미지 문제 유형

| 유형 | 설명 | 감지 방법 |
|------|------|-----------|
| **URL 404** | 이미지 URL이 더 이상 유효하지 않음 | curl로 HTTP 상태 확인 |
| **리다이렉트 루프** | URL이 무한 리다이렉트됨 | 응답 헤더 확인 |
| **접근 차단** | 403 Forbidden (핫링크 방지) | HTTP 상태 코드 확인 |
| **비이미지 콘텐츠** | URL이 이미지가 아닌 HTML 페이지 반환 | Content-Type 헤더 확인 |
| **이미지 누락** | 스팟에 이미지가 아예 없음 | 페이지 콘텐츠에 `![` 패턴 부재 확인 |
| **Notion 렌더링 실패** | URL은 유효하나 Notion에서 표시 불가 | 특정 도메인 패턴 확인 |

### Notion에서 잘 작동하는 이미지 소스

| 소스 | 안정성 | 비고 |
|------|--------|------|
| **Pexels CDN** | ✅ 높음 | `images.pexels.com` — 권장 |
| **Unsplash CDN** | ✅ 높음 | `images.unsplash.com` |
| **Imgur** | ✅ 높음 | `i.imgur.com` |
| **Wikimedia** | ⚠️ 중간 | `upload.wikimedia.org` — 가끔 차단 |
| **Google Images** | ❌ 낮음 | 핫링크 차단, 빈번한 URL 변경 |
| **개인 블로그** | ❌ 낮음 | 서버 다운, 핫링크 차단 |

## 검증 워크플로우

### Phase 1: 이미지 URL 수집

```
1. 대상 Notion 페이지 목록 확보
   - 파이프라인 내: travel-image-search가 전달한 페이지 ID 목록
   - 독립 실행: 사용자가 지정한 Notion 페이지 또는 메인 페이지에서 서브 페이지 추출

2. 각 페이지를 fetch로 읽기
   - 페이지 콘텐츠에서 이미지 마크다운 패턴 추출
   - 패턴: ![{alt text}]({image_url})
   - 각 이미지의 위치(스팟명)와 URL을 목록화

결과: 이미지 목록 [{page_id, spot_name, alt_text, url, position}]
```

### Phase 2: URL 유효성 검증

```
각 이미지 URL에 대해:

1. URL 패턴 사전 검사
   - Pexels CDN 형식인지 확인 (images.pexels.com)
   - 알려진 불안정 도메인인지 확인
   - URL 파라미터 정상 여부 확인

2. HTTP 접근성 검사 (Bash curl 활용)
   curl -sI -o /dev/null -w "%{http_code}" --max-time 5 "{image_url}"

   - 200: ✅ 정상
   - 301/302: ⚠️ 리다이렉트 (최종 URL 확인 필요)
   - 403: ❌ 접근 차단 → 교체 필요
   - 404: ❌ 삭제됨 → 교체 필요
   - 000/timeout: ❌ 서버 무응답 → 교체 필요

3. Content-Type 확인
   curl -sI --max-time 5 "{image_url}" | grep -i "content-type"

   - image/jpeg, image/png, image/webp: ✅ 정상
   - text/html: ❌ 이미지가 아니→ 교체 필요

결과: 검증 결과 [{url, status, issue_type, needs_replacement}]
```

### Phase 3: 문제 이미지 교체

```
needs_replacement가 true인 각 이미지에 대해:

1. 대체 이미지 검색
   - WebSearch: "site:pexels.com {스팟명 영문} landscape"
   - 결과에서 Pexels 사진 ID 추출
   - CDN URL 생성: https://images.pexels.com/photos/{ID}/pexels-photo-{ID}.jpeg?auto=compress&cs=tinysrgb&w=1280

2. 대체 이미지 검증
   - 새 URL도 동일한 검증 절차 수행
   - 실패 시 다른 검색 키워드로 재시도 (최대 3회)
   - 최종 실패 시 이미지 제거 (텍스트만 유지)

3. Notion 페이지 업데이트
   - notion-update-page의 update_content 사용
   - old_str: "![{기존 alt}]({기존 URL})"
   - new_str: "![{스팟명}]({새 Pexels URL})"

4. 업데이트 확인
   - fetch로 페이지 재확인
   - 새 이미지가 정상 삽입되었는지 검증
```

### Phase 4: 누락 이미지 추가

```
이미지가 아예 없는 스팟에 대해:

1. 페이지 콘텐츠에서 스팟 섹션 식별
   - "## 📍 {스팟명}" 또는 "### {스팟명}" 패턴 찾기

2. 해당 스팟의 이미지 검색
   - travel-image-search 스킬과 동일한 검색 전략
   - Pexels CDN URL 확보 및 검증

3. 이미지 삽입
   - 스팟 제목 바로 아래에 이미지 마크다운 추가
   - notion-update-page로 삽입
```

## 검증 보고서

검증 완료 후 결과를 요약합니다:

```markdown
## 🔍 이미지 검증 결과

### 요약
- 총 검사 이미지: {N}개
- ✅ 정상: {N}개
- 🔄 교체 완료: {N}개
- ➕ 신규 추가: {N}개
- ❌ 해결 불가: {N}개

### 교체 내역
| 페이지 | 스팟 | 문제 | 조치 |
|--------|------|------|------|
| Day 2 | {스팟명} | 404 Not Found | Pexels 이미지로 교체 |
| Day 3 | {스팟명} | 이미지 누락 | 신규 이미지 추가 |

### 수동 확인 필요
- {해결되지 않은 항목 설명}
```

## 파이프라인 통합

### 오케스트레이터에서의 위치

```
③ travel-image-search    — Pexels 이미지 검색 & 삽입
    ↓
③-1 travel-image-validator — 삽입된 이미지 검증 & 수정 ← 여기
    ↓
④ travel-content-enrichment — 6가지 상세 콘텐츠 보강
```

### 자동 실행 조건

- travel-image-search 완료 후 자동 트리거
- 독립 실행: 사용자가 명시적으로 요청하거나, 기존 페이지 점검 시

### 입출력

```
입력:
  - page_ids: Notion 페이지 ID 목록
  - spot_list: 스팟 이름 목록 (이미지 검색 키워드용)

출력:
  - validation_report: 검증 결과 요약
  - replaced_count: 교체된 이미지 수
  - added_count: 추가된 이미지 수
  - failed_items: 해결 불가 항목 목록
```

## 독립 실행 모드

기존 Notion 여행 페이지의 이미지를 사후 점검할 때:

```
1. 사용자에게 Notion 페이지 URL 또는 제목 요청
2. search로 해당 페이지 찾기
3. 메인 페이지에서 서브 페이지 목록 추출
4. 전체 검증 워크플로우 실행 (Phase 1-4)
5. 검증 보고서 출력
```

## 배치 검증 최적화

```
1. 동일 도메인 URL 그룹핑
   - Pexels CDN → 높은 확률로 정상, 샘플 검증
   - 비 Pexels → 전수 검증

2. 병렬 검증 (Agent tool 활용)
   - 페이지별로 Agent 분배
   - 각 Agent가 담당 페이지의 이미지 검증 + 교체

3. 캐시 활용
   - 이미 검증된 URL은 재검증 스킵
   - 검증 결과를 /tmp/image_validation_cache.json에 임시 저장
```

## 오류 처리

| 상황 | 대응 |
|------|------|
| Notion fetch 실패 | 재시도 3회, 실패 시 해당 페이지 스킵 |
| 모든 대체 이미지 실패 | 해당 스팟 이미지 제거, 보고서에 기록 |
| update_content 실패 | 정확한 old_str 재확인 후 재시도, 실패 시 스킵 |
| curl 타임아웃 | 5초 제한, 타임아웃 시 교체 대상으로 분류 |

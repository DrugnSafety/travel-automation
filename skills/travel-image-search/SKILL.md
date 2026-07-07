---
name: travel-image-search
description: 여행 관광지의 실제 모습과 일치하는 이미지를 찾아 눈으로 검증한 뒤 Notion 페이지에 안정적으로 삽입합니다. Wikimedia Commons API로 랜드마크 정확도가 보장된 이미지를 우선 확보하고, 삽입 전 반드시 이미지를 직접 열어 관련성을 시각 확인하며, Notion 첨부 업로드로 핫링크 깨짐을 원천 차단합니다. 사용자가 여행 사진 추가, 노션 이미지 삽입, 관광지 사진 찾기, 이미지 교체 등을 요청할 때 이 스킬을 사용하세요.
---

# Travel Image Search v3

관광지 이미지를 **정확하게 찾고 → 눈으로 확인하고 → 깨지지 않게 삽입**하는 스킬.

## v2의 실패 원인 (반복 금지)

| v2 방식 | 문제 |
|---------|------|
| WebSearch 결과에서 Pexels 사진 ID를 추출해 CDN URL 조립 | 검색 결과에 실제 ID가 없어 **존재하지 않는 URL을 지어냄** → 404 깨짐 |
| Pexels 스톡사진을 랜드마크 대표 이미지로 사용 | "Horseshoe Bend" 검색에 일반 협곡 사진이 걸림 → **관련 없는 이미지 삽입** |
| 삽입 후에만 HTTP 검증 | URL이 살아있어도 **내용이 엉뚱한지는 아무도 확인 안 함** |

**철칙: 단 한 장도 눈으로 확인하지 않은 이미지를 Notion에 넣지 않는다.**

## 이미지 소스 우선순위 (랜드마크 정확도 순)

### 1순위: Wikipedia REST API (특정 랜드마크의 대표 사진)

문서 대표 이미지 = 그 장소가 맞다는 것이 커뮤니티에 의해 이미 검증된 사진.

```bash
curl -s "https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('originalimage',{}).get('source',''))"
```

- `wiki_title`은 plan JSON의 `wiki_title` 필드 사용 (예: `Horseshoe_Bend_(Arizona)`)
- 반환 URL은 `upload.wikimedia.org` 직링크 — **리다이렉트 없음, HTTP 200, image/jpeg 확인됨**
- 원본이 너무 크면 URL의 `/{width}px-` 부분을 `1600px`로 조정

### 2순위: Wikimedia Commons 검색 API (대표 사진 외 추가 컷)

```bash
curl -s "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={장소명}&gsrnamespace=6&gsrlimit=5&prop=imageinfo&iiprop=url|mime|size&iiurlwidth=1280&format=json"
```
- 응답의 `thumburl`(1280px 직링크)을 사용. 파일명(title)에 장소명이 포함된 것 우선.

### 3순위: 공식 기관 이미지
- 미국 국립공원: NPS 공식 사이트(`nps.gov`) 이미지 — 퍼블릭 도메인
- 관광청 공식 사이트 이미지

### 4순위: Pexels/Unsplash (분위기 컷 전용)
- **특정 랜드마크에는 사용 금지.** "사막 로드트립 풍경", "가족 캠핑" 같은 일반 분위기 컷에만 허용.
- 반드시 실제 페이지를 WebFetch로 열어 진짜 사진 ID를 확인한 후 CDN URL 구성. ID 추측 조립 금지.

### 5순위: AI 생성 이미지
- 실사 확보 실패 시 또는 사용자가 특정 스타일을 원할 때 → **travel-image-generator** 스킬로 위임.

## 필수 워크플로우: 다운로드 → 시각 검증 → 삽입

### Step 1: 후보 확보 (스팟당 2~3장)
위 우선순위로 후보 URL 확보 후 로컬 다운로드:
```bash
curl -sL --max-time 15 -o /tmp/img_check/{스팟명}_{n}.jpg "{URL}"
```

### Step 2: 시각 검증 (핵심 — 절대 생략 금지)
다운로드한 이미지를 **Read 도구로 직접 열어 눈으로 확인**한다:

```
체크리스트 (하나라도 실패 시 해당 후보 탈락):
□ 이 사진이 정말 {스팟명}인가? (지형·건물·표지판이 해당 장소 특징과 일치)
□ 화질이 충분한가? (블러·저해상도·워터마크 없음)
□ 대표 이미지로 적절한가? (공사장면·군중만 찍힌 컷·실내 잡사진 아님)
□ 가족 가이드북에 적합한가?
```

여러 후보 중 가장 좋은 1장을 선택. 전부 탈락하면 다음 순위 소스로 재시도 (최대 3회), 최종 실패 시 travel-image-generator로 넘기거나 이미지 없이 진행하고 보고서에 기록.

### Step 3: Notion 삽입 — 첨부 업로드 우선

**방법 1 (권장): Notion 첨부 업로드** — 외부 서버가 죽어도 안 깨짐
```
notion-create-attachment {"filename": "{스팟명}.jpg", "source_url": "{검증된 직링크}"}
→ 응답의 markdown_source (file-upload://...) 획득
→ 1시간 내에 notion-update-page / notion-create-pages 콘텐츠에 배치:
   ![{스팟명}](file-upload://...)
```
- source_url 조건: 리다이렉트 없음, 쿠키/헤더 불필요, 50MB 이하 — upload.wikimedia.org는 충족(검증됨)
- 업로드 실패(용량·리다이렉트) 시 방법 2로 폴백

**방법 2 (폴백): 외부 URL embed**
```markdown
![{스팟명}]({검증된 직링크})
```
- 허용 도메인: `upload.wikimedia.org`, `images.pexels.com`, `images.unsplash.com`, `nps.gov`
- 삽입 직전 curl HEAD로 `HTTP 200 + Content-Type: image/*` 재확인

### Step 4: 캡션과 배치
- 이미지 바로 아래 캡션: 장소명 + 특징 한 줄 (예: "홀슈벤드 — 콜로라도강이 270° 휘감는 절벽")
- 배치 규칙: 메인 페이지 히어로 1장, Day 페이지 스팟당 1장 (스팟 제목 H2 바로 아래)
- Notion 마크다운 이미지 문법과 위치는 notion-travel-page 템플릿 사양을 따름

## 히어로 이미지 스타일 질문 (파이프라인 시작 시 1회)

메인 페이지 히어로와 표지성 이미지는 **작업 시작 전 AskUserQuestion으로 스타일을 확인**한다:

```
질문: "메인 페이지 대표 이미지는 어떤 스타일로 할까요?"
옵션:
  1. 실사 사진 (Wikipedia/공식 이미지) — 기본 권장
  2. 시네마틱 AI 생성 (영화 포스터풍)
  3. 수채화/일러스트 AI 생성 (가이드북 감성)
  4. 미니멀 인포그래픽 AI 생성 (동선 지도 스타일)
```
- 2~4 선택 시 travel-image-generator 스킬로 위임 (스타일 값 전달)
- 스팟별 본문 이미지는 항상 실사 우선 (예습 목적 — 실제 모습을 봐야 함)

## 검증 기록

모든 삽입 이미지를 `/tmp/{여행지}_images.json`에 기록 — validator와 PPT 단계가 재사용:
```json
[{"spot": "Horseshoe Bend", "page_id": "...", "source": "wikipedia",
  "url": "https://upload.wikimedia.org/...", "method": "attachment|embed",
  "visual_check": "pass — 말굽형 협곡 확인", "local_copy": "/tmp/img_check/..."}]
```

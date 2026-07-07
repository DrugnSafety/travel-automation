---
name: travel-image-generator
description: 여행지 대표 이미지, 일정표 카드, 짐 싸기 체크리스트, 주의사항 카드, 아이용 예습 매거진 등을 위한 AI 이미지 생성 프롬프트를 제작합니다. 사용자의 노션 프롬프트 라이브러리에서 추출한 19종 스타일 체계를 기반으로, 먼저 사용자에게 원하는 스타일을 물어본 뒤 완성형 프롬프트를 생성합니다. 사용자가 이미지 만들어줘, 대표 사진 생성, 여행 포스터, 일정표 이미지, 체크리스트 이미지, AI 그림 등을 요청할 때 이 스킬을 사용하세요.
---

# Travel Image Generator

실사 이미지 대신(또는 함께) **AI 생성 이미지**가 필요할 때, 검증된 스타일 라이브러리 기반으로 프롬프트를 만들어 이미지를 생성하는 스킬.

원본 라이브러리: 사용자 노션 "Prompt" DB (`https://app.notion.com/p/35002c77e2c98030acb9f50204fbf60d`) — 프롬프트 전문이 필요하면 이 DB를 fetch해서 해당 스타일의 원문을 그대로 활용한다.

## Step 1: 스타일 질문 (필수 — 생성 전에 반드시 물어본다)

AskUserQuestion으로 용도와 스타일을 확인한다. 이미 파이프라인 초기에 답을 받았으면 재질문하지 않는다.

```
질문 1: "어떤 용도의 이미지인가요?" (파이프라인이면 자동 결정)
질문 2: "어떤 스타일을 원하세요?"
  옵션 (용도별로 아래 표에서 3~4개 추려 제시, 각 옵션에 한 줄 설명):
  - 일러스트 감성: 수채화 / 감성 스케치 / 파스텔 콜라주 / 시네마틱 일몰
  - 인포·실용: 아이소메트릭 가이드 / 백과사전 카드 / 체크리스트 / 다이어리 일정표
  - 키즈: 키즈 매거진 / 스칸디 그림책
  - 포스터·타이포: 레트로 플랫 / 타이포그래피 / 토이 시티
```

선택 규칙:
- 사용자가 "전체 목록 보여줘"라고 하면 아래 **노션 Prompt DB 항목 카탈로그**의 항목명을 그대로 나열해 고르게 한다.
- 스타일이 확정되면 **카탈로그의 해당 노션 페이지를 fetch해 프롬프트 원문을 그대로 사용**한다 (원문이 항상 1순위, Step 3 마스터 템플릿은 원문이 없거나 여행 데이터 주입이 필요할 때의 보강용).

## Step 1.5: 노션 Prompt DB 항목 카탈로그 (2026-07-07 동기화, 22행)

DB: `collection://35002c77-e2c9-80c4-803d-000b581cfb57` (새 항목이 추가될 수 있으므로, 카탈로그에 없는 요청이면 DB를 재조회한다)

| DB 항목명 | 스타일 키 | 노션 페이지 |
|-----------|----------|-------------|
| 여행 스케지 - 화사하고 밝은 컨셉 | `watercolor-bright` | app.notion.com/38202c77e2c9808ca922d566aa5e7844 |
| 여행 스케지 - 랜드마크 빈티지 컨셉 | `sketch-vintage` | app.notion.com/38202c77e2c980aab562c44e07c644fb |
| 여행 스케치 - 일몰 풍경 포스터 | `cinematic-sunset` | app.notion.com/38202c77e2c9802d914ce68d4c002fee |
| 여행 스케치 - 파스텔 페이퍼 콜라주 여행 포스터 | `paper-collage-pastel` | app.notion.com/38202c77e2c98027bafcd60da5d177e2 |
| 여행 스케치 - 민트·피치·코랄 파스텔 선셋 레트로-모던 | `retro-modern-flat` | app.notion.com/38202c77e2c9809690a9d639060abe68 |
| 여행 스케치 - 깔끔한 미니멀리즘 페이퍼 아트 포스터 | `minimal-paper-white` | app.notion.com/38202c77e2c980078774edf44ce6b416 |
| 여행 스케치 - 미니어처 토이 시티 프리미엄 여행 포스터 | `toy-city-vector` | app.notion.com/38202c77e2c9808586cdd71561a5a627 |
| 여행 장소 - 레고 스타일 아키텍쳐 | `toy-city-vector` 변형 | app.notion.com/38202c77e2c980418fcdc65a128066cb |
| 여행 스케치 - 목적지 Typo 안에 풍경 포스터 | `typography-poster` | app.notion.com/38202c77e2c980a582b2d8cfdaaff8ef |
| 여행 스케치 - Beams 영감 미니멀리즘 포스터 | `monoline-street` | app.notion.com/38202c77e2c9803792cfcbc3f0e215c2 |
| 여행 스케치 - 애플 감성 건축 도면 (16:9·한국어) | `blueprint-apple` | app.notion.com/38202c77e2c980259f20d52cff1157ea |
| 여행 스케치 - 글로벌 시티 가이드 아이소메트릭 인포그래픽 | `isometric-city-guide` | app.notion.com/38202c77e2c9805f9658fd181c619c17 |
| 여행 스케치 - 브리태니커 백과사전 인포그래픽 | `encyclopedia-infographic` | app.notion.com/38202c77e2c98034afddd2443ea98337 |
| 여행 장소 - 역사 스케치 | `history-timeline` | app.notion.com/38202c77e2c980bf812dfcfe0ab9ecb5 |
| 여행 스케치 - 프리미엄 매거진×코믹 고밀도 인포그래픽 가이드 | `comic-infographic` | app.notion.com/38202c77e2c98017a8c7eca97652cd0d |
| 여행 스케치 - 만능 여행 준비 프리미엄 체크리스트 | `checklist-minimal` | app.notion.com/38202c77e2c9800d9f12c916c06875d4 |
| 여행 일정 이미지/예산 | `diary-itinerary` | app.notion.com/35002c77e2c9806cad00dde3e7649ffc |
| 여행 스케치 - 키즈 여행 매거진 스타일 | `kids-magazine` | app.notion.com/38202c77e2c9803d8f85cc343a57f518 |
| 여행 스케치 - 유아를 위한 덴마크 여행작가 스타일 | `kids-geometric` | app.notion.com/38202c77e2c98057bae0e1fd353e1c4d |
| 인스타 감성 손글씨 메모 (음식·메뉴판) | `handwriting-overlay` | app.notion.com/35002c77e2c98039b56ceda883ad01b2 |
| 🧥 OOTD용 감성 손글씨 메모 (한글판) | `handwriting-overlay` 변형 | app.notion.com/35002c77e2c980eba631fab657930b2e |
| Codex - PPT 발표자료 제작 프롬프트 8종 | (이미지 아님 → travel-presentation 참조) | app.notion.com/39502c77e2c981289d60e89ea7846325 |

## Step 2: 스타일 라이브러리 (19종)

| 스타일 키 | 설명 | 최적 용도 | 비율 |
|-----------|------|-----------|------|
| `watercolor-bright` | 일본 에디토리얼 수채화, 빛 중심 거리 풍경 | 히어로, 블로그 커버 | 4:5 |
| `sketch-vintage` | 연필+과슈 스케치북, 저채도 | 히어로, Day 헤더 | 4:5 |
| `cinematic-sunset` | 랜드마크 1개 중심 향수풍 관광 포스터 | 히어로 | 4:5 |
| `paper-collage-pastel` | 페이퍼컷 레이어 포스터 | 여행지 포스터 | 4:5 |
| `retro-modern-flat` | 미드센추리 플랫 벡터, 민트·피치·코랄 | 포스터, PPT 표지 | 4:5 |
| `minimal-paper-white` | 흰 배경 미니멀 페이퍼 아트 | 포스터 | 9:16 |
| `toy-city-vector` | 랜드마크 8~15개 벡터 콜라주 | 도시 개요 | 4:5 |
| `typography-poster` | 도시명 글자 안에 풍경 | PPT 타이틀, 배너 | 16:9 |
| `monoline-street` | 단색 라인아트 일상 거리 | 감성 포스터 | 세로 |
| `blueprint-apple` | 애플 감성 건축 도면 (한국어) | 랜드마크 상세 | 16:9 |
| `isometric-city-guide` | 애플 미니멀 아이소메트릭 인포그래픽 (한국어) | 도시 요약 | 4:5 |
| `encyclopedia-infographic` | 백과사전식 지식 카드 (한국어) | 지질·동식물 교육 카드 | 세로 |
| `history-timeline` | 12패널 스위스 그리드 역사 타임라인 (한국어, 실제 사건만) | 역사/문화 배경 | 4:5 |
| `comic-infographic` | 위트있는 코믹+인포그래픽 가이드 (한국어) | 실전 팁·주의사항 | 4:5 |
| `checklist-minimal` | A4 출력용 체크박스+아이콘 리스트 (한국어) | 짐 싸기 | A4 |
| `diary-itinerary` | 파스텔 손그림 DAY별 일정+예산 콜라주 | 일정표 이미지 | 4:5 |
| `kids-magazine` | 일본 어린이 잡지 스프레드, 7개 코너 (한국어, 초등용) | 아이 예습 자료 | 4:3 |
| `kids-geometric` | 찰리 하퍼풍 기하학 그림책, 랜드마크 3개 | 아이용 페이지 | 세로 |
| `handwriting-overlay` | 사용자 사진 위 흰 손글씨 한국어 메모 | 여행 후 사진 꾸미기 | 원본 |

### 산출물 유형 → 기본 스타일 자동 매핑 (사용자가 "알아서 해줘" 할 때)

| 산출물 | 기본 스타일 |
|--------|------------|
| 여행지 대표(히어로) | `cinematic-sunset` 또는 `watercolor-bright` |
| 여행 일정표 | `diary-itinerary` |
| 짐 싸기 준비물 | `checklist-minimal` |
| 여행 주의사항 | `comic-infographic` |
| 서현이(아이) 예습 카드 | `kids-magazine` |
| 지질·역사 학습 카드 | `encyclopedia-infographic` / `history-timeline` |
| PPT 표지 | `typography-poster` / `retro-modern-flat` |

## Step 3: 프롬프트 조립 — 마스터 템플릿

```
Create a premium {format} of {destination}, in the style of {style_anchor}.

MAIN CONCEPT
Center on {focal_rule}. Capture {emotional_goal} rather than documentary accuracy.
This must NOT look like {anti_reference}.

STYLE
{style_keywords 8~15개}. No photorealism, no 3D rendering, no clutter.

COLOR PALETTE
Limited palette (4–6 colors): {palette_keywords}. Automatically adapt accent colors
to {destination}'s climate, environment, and cultural identity. Avoid oversaturated neon.

LIGHTING / COMPOSITION
{lighting}. {aspect_ratio} layout, clear foreground/midground/background layering,
generous negative space. {layout_specifics}

TYPOGRAPHY & TEXT
Language: {Korean for 정보형 | English for 포스터형}. Destination name in clean
geometric sans-serif, wide letter spacing. All text must be perfectly spelled —
no distorted letters, no random characters, no AI-generated gibberish.

{CONTENT SECTIONS — 인포그래픽·체크리스트·매거진 형식만}
{content_slots}, auto-adapted to {destination} and {audience}.

MOOD / QUALITY
{mood_keywords}. 8K ultra-high resolution, print-ready, ultra clean edges, museum-grade finish.
```

조립 규칙:
1. **랜드마크 정확도 조항 필수**: 히어로·포스터형에는 "The landmark must remain visually accurate and immediately recognizable from its most iconic angle. Avoid fantasy redesigns." 삽입.
2. **타이포 무결성 조항 필수**: 모든 스타일에 anti-gibberish 조항 포함 (프롬프트 DB 전 항목 공통 패턴).
3. **비율은 용도로 결정**: Notion 히어로 4:5 · PPT 16:9 · 출력물 A4.
4. **정보형(일정표·체크리스트·주의사항)은 실제 여행 데이터 주입**: plan JSON의 실제 날짜·스팟명·금액을 CONTENT SECTIONS에 구체적으로 넣는다. 일반 문구 금지.
5. 아이 대상물은 초등 4학년(만 9~10세) 눈높이 명시.

## Step 4: 생성 — OpenAI gpt-image-2 API (기본 경로, 검증 완료)

API 키는 `~/.config/travel-automation/openai.env`에서 로드한다 (**키를 채팅·플러그인 파일·메모리에 절대 기록하지 않는다**):

```bash
source ~/.config/travel-automation/openai.env
curl -s --max-time 180 https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model": "'"$OPENAI_IMAGE_MODEL"'", "prompt": "{조립한 프롬프트}",
       "size": "{사이즈}", "quality": "{품질}", "n": 1}' > /tmp/gen.json
python3 -c "import json,base64; open('/tmp/gen_{이름}.png','wb').write(base64.b64decode(json.load(open('/tmp/gen.json'))['data'][0]['b64_json']))"
```

| 용도 | size | quality |
|------|------|---------|
| Notion 히어로·포스터 (4:5 근사) | `1024x1536` (세로) | `medium` |
| PPT 표지·와이드 (16:9 근사) | `1536x1024` (가로) | `medium` |
| 시안·드래프트 확인용 | `1024x1024` | `low` |
| 최종 인쇄물 (체크리스트 A4 등) | `1024x1536` | `high` |

- 시안은 `low`로 먼저 뽑아 사용자 확인 → 확정 후 `medium/high` 재생성 (비용 절약)
- 응답에 `error.code`가 있으면(쿼터·차단) 메시지를 확인하고 사용자에게 보고 — 다른 등록 키로의 자동 전환은 하지 않는다
- API 자체가 실패하면 폴백: 완성 프롬프트를 코드블록으로 사용자에게 전달 (ChatGPT 앱 등에서 직접 생성)

## Step 5: 검증 및 Notion 삽입

1. **시각 검증 필수**: 생성 PNG를 Read로 열어 확인 — 텍스트 오탈자(AI 특유의 깨진 글자), 랜드마크 왜곡, 스타일 일치. 텍스트 깨짐 → 재생성 1회, 재실패 시 텍스트 없는 스타일로 전환.
2. **Notion 삽입** (로컬 파일 → 공개 URL → 영구 첨부 체인, 검증 완료):
   ```bash
   curl -s -F "reqtype=fileupload" -F "fileToUpload=@/tmp/gen_{이름}.png" https://catbox.moe/user/api.php
   # → https://files.catbox.moe/xxxx.png (사용자 노션에서 기존 사용 중인 호스트)
   ```
   반환 URL을 `notion-create-attachment`의 `source_url`로 업로드 → `file-upload://` 소스로 삽입 (Notion 영구 호스팅). 첨부 실패 시 catbox URL 직접 embed 폴백.
3. **주의**: catbox는 공개 호스팅 — AI 생성 포스터·인포그래픽만 업로드. **가족 사진 등 개인 이미지는 절대 금지** (handwriting-overlay 스타일 결과물 포함).

## 산출물 기록

생성한 프롬프트와 결과물을 `/tmp/{여행지}_genimages.json`에 기록하고, 좋았던 프롬프트 변형은 사용자 승인 후 노션 Prompt DB에 새 행으로 추가 제안한다 (notion-create-pages, data_source: `collection://35002c77-e2c9-80c4-803d-000b581cfb57`).

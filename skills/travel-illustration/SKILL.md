---
name: travel-illustration
description: gpt-image-2로 여행 가이드용 오리지널 일러스트를 생성해 노션 페이지에 삽입하는 스킬. 여정 전체를 한 장에 담은 요약 일러스트와, 날짜별로 그날의 동선·주요 방문지·시간대·계절감을 반영한 삽화를 만든다. 사용자가 여행 그림 생성, 일러스트, AI 이미지, 날짜별 이미지, 여정 요약 그림, 표지 그림, gpt-image-2 등을 언급할 때 사용. 스톡 사진(Pexels)의 대체재가 아니라 별도 산출물이며, 둘 다 생성한다.
---

# Travel Illustration — gpt-image-2 여행 삽화

## 이것이 무엇인지 먼저 분명히 한다

| | AI 일러스트 (이 스킬) | 스톡 사진 (`travel-image-search`) |
|---|---|---|
| 무엇 | 그날의 동선·일정을 한 장에 요약한 **오리지널 삽화** | 실제 장소의 **사진** |
| 개수 | 여정 1장 + 날짜당 1장 | 스팟당 2장 이상 |
| 위치 | 각 페이지 **최상단** | 각 스팟 섹션 안 |
| 관계 | **서로를 대체하지 않는다. 둘 다 만든다.** | |

> 과거에 이 구분이 모호해 "Pexels에서 못 찾은 사진을 AI로 대체 생성"으로 잘못 이해하고 전량 재생성한 사례가 있다. 일러스트는 **정보 시각화**이지 사진 대용이 아니다.

---

## 사전 조건

API 키는 `OPENAI_API_KEY` 환경변수 또는 `~/.config/gpt-image/.env`에서 읽는다.

```bash
mkdir -p ~/.config/gpt-image
printf 'OPENAI_API_KEY=sk-...\n' > ~/.config/gpt-image/.env
chmod 600 ~/.config/gpt-image/.env
```

**키를 대화창에 붙여넣도록 요구하지 않는다.** 사용자가 붙여넣었다면 즉시 파일로 옮기고, **해당 키는 대화 로그에 노출되었으므로 폐기하고 새로 발급하라고 안내한다.**

생성 전 `--dry-run`으로 요청 내용과 잔여 한도를 확인한다. 생성은 유료다. **여러 장을 뽑기 전에 1장으로 방향을 먼저 확인받는다.**

키가 여러 개면 크레딧 소진(`429 credit_balance_exhausted`)에 대비해 순환 사용한다.

---

## 산출물 1 — 여정 전체 요약 일러스트

메인 페이지 상단에 들어간다. 전체 동선이 한눈에 읽히는 **일러스트 지도(illustrated map)** 형식이 가장 효과적이다.

### 프롬프트 템플릿

```
A hand-drawn illustrated travel map poster summarizing an entire {N}-day family road
trip across {지역}. Digital watercolor with clean ink line art, warm {계절 팔레트}.
Wide 16:9 composition, bird's-eye stylized map perspective.

The route is drawn as a {색상} dashed line winding across the map from {출발지} to
{도착지}, with {N} numbered circular markers along it.

Landmark vignettes drawn along the route in order:
1. {랜드마크 1} — {한 줄 시각 묘사}
2. {랜드마크 2} — {한 줄 시각 묘사}
... (최대 8개)

Small recurring motifs: {차량 종류}, {대표 야생동물}, {계절 요소}.

A hand-lettered title banner at the top reads: "{여행명}"
A small legend at the bottom right shows: "{기간} · {거리} · {인원 구성}"

Mood: {여행의 정서}. Warm, inviting, keepsake quality — something a family would
frame after the trip.

Do NOT include: photorealistic style, distorted hands or faces, blurry or misspelled
text, watermarks, modern UI elements.
```

**지명 텍스트는 최소화한다.** gpt-image-2는 이미지 내 텍스트 렌더링이 강한 편이지만, 여러 개의 고유명사를 동시에 넣으면 철자가 깨진다. 제목 배너 하나와 짧은 범례 정도가 안전선이다.

---

## 산출물 2 — 날짜별 일러스트

각 날짜 페이지 상단에 들어간다. **그날의 정보가 그림 안에 담겨야 한다.**

### 반드시 반영할 4가지

**① 동선 순서**
그날 방문하는 장소를 실제 순서대로 배치한다. 왼쪽→오른쪽 또는 위→아래 구성이 읽기 쉽다.

**② 시간대**
장소마다 실제 방문 시각의 광질(光質)을 반영한다. 이것이 날짜별 일러스트를 서로 구별되게 만드는 가장 강력한 요소다.

| 시각 | 프롬프트 표현 |
|---|---|
| 05:00~07:00 | `pre-dawn blue hour, mist rising, low warm rim light` |
| 07:00~10:00 | `crisp morning light, long shadows, clear air` |
| 10:00~15:00 | `high midday sun, saturated colors, short shadows` |
| 15:00~18:00 | `golden hour, long amber shadows` |
| 18:00~20:00 | `sunset, orange-to-violet gradient sky` |
| 20:00 이후 | `deep twilight, artificial lighting, first stars` |

**③ 계절 특성**
`trip-brief.json`의 `season.traits`를 그대로 시각 요소로 바꾼다.

| 계절 | 시각 요소 |
|---|---|
| 늦여름 (8월) | 황금빛 마른 초원, 짙은 상록수, 오후 뭉게구름과 먼 소나기, 야생화 끝물 |
| 초가을 (9~10월) | 노란 아스펜, 엘크 발정기, 첫서리, 낮은 태양각 |
| 겨울 | 눈 덮인 능선, 김이 오르는 온천, 앙상한 나무, 창백한 하늘 |
| 봄 | 잔설, 불어난 계곡물, 새끼 동물, 신록 |

**④ 시간 정보 표기**
배너와 하단 범례에 시각을 넣는다.

```
At the top, a hand-lettered banner reads: "Day {N} · {월}/{일} ({요일}) · {구간 요약}"
At the bottom, three small time labels along the route:
"{시각1} {장소1}" · "{시각2} {장소2}" · "{시각3} {장소3}"
```

### 프롬프트 템플릿

```
A warm storybook-style travel guide illustration for Day {N} of a family {여행 유형}.
Digital watercolor with clean line art, {계절 팔레트}. Wide 16:9 cinematic composition.

Scene composition (left to right, following the day's route):
- Left:   {아침 장소} at {아침 광질}. {구체적 시각 묘사}
- Middle: {낮 장소} at {낮 광질}. {구체적 시각 묘사}
- Right:  {저녁 장소} at {저녁 광질}. {구체적 시각 묘사}

Foreground: {인원 구성 묘사 — 개인 식별 불가능한 일반화된 표현}, seen from behind
or in three-quarter view.

Seasonal details: {계절 요소 2~3개}

At the top, a hand-lettered title banner reads: "Day {N} · {월}/{일} ({요일}) · {구간}"
At the bottom, small time markers: "{시각1} {장소1}" · "{시각2} {장소2}" · "{시각3} {장소3}"

Mood: {그날의 정서}

Do NOT include: photorealistic style, distorted hands or faces, blurry or misspelled
text, watermarks.
```

### 인물 묘사 원칙

- 실존 인물을 지칭하거나 특정인을 닮게 만들지 않는다
- 일반화된 표현을 쓴다: `a family of four — two adults, an elementary-aged child, and a grandparent`
- 얼굴은 뒷모습이나 3/4 측면으로 처리해 왜곡 위험을 줄인다
- 실명·나이·사진은 프롬프트에 넣지 않는다 (외부 API로 전송된다)

---

## 실행

### 1. 프롬프트 작성

`trip-brief.json`과 각 날짜의 타임라인을 읽어 `/tmp/{trip_slug}/assets/prompts/` 아래에 파일로 저장한다.

```
prompts/overview.txt
prompts/day01.txt ... prompts/day{N}.txt
```

`gpt-image-prompt-picker` 스킬이 설치돼 있으면 코퍼스에서 형식이 맞는 후보를 먼저 검색한다. `match_quality: weak`이면 억지로 쓰지 말고 위 템플릿으로 직접 작성한다.

### 2. 생성

`moai-media` 계열 스킬(`media-gpt-image2-builder`, `image-gen`)이 있으면 위임한다. 없으면:

```bash
python3 ~/.claude/skills/gpt-image-prompt-picker/scripts/generate.py \
  --prompt-file prompts/day01.txt \
  --size 1536x1024 \
  --label day01 \
  --out /tmp/{trip_slug}/assets/illustrations
```

- 크기: 노션 페이지 상단은 **1536x1024 (16:9)** 가 적합
- 하루 상한 기본 30장 (`GIP_DAILY_LIMIT`)
- 2~3장씩 나눠 실행한다. 한 번에 10장 이상 요청하면 rate limit에 걸린다.

### 3. 노션 업로드 및 삽입

```
notion-create-file-upload  → file_upload_id 획득
```

페이지 최상단에 삽입한다.

```markdown
<image src="file-upload://{file_upload_id}">Day {N} — {구간 요약}</image>
```

> ⚠️ 외부 URL을 페이지 아이콘으로 넣으면 `Invalid page icon URL` 오류가 난다. **아이콘은 이모지**, 커버는 외부 이미지 URL을 쓴다.

### 4. 상태 기록

`state.json`의 `illustrations`에 `{day, prompt_path, image_path, file_upload_id, inserted}`를 남긴다. 재실행 시 이미 생성된 것을 다시 만들지 않는다.

---

## 게이트

- 요약 1장 + 날짜별 전량이 존재하는가
- 각 이미지가 노션 파일 업로드 ID를 갖고 페이지에 삽입되었는가
- 배너 텍스트의 날짜·요일이 `day_map`과 일치하는가 (**이미지를 실제로 열어 확인한다** — 모델이 철자를 틀리는 경우가 있다)

배너 텍스트가 깨졌으면 해당 장만 재생성한다. 텍스트를 더 짧게 줄이면 성공률이 올라간다.

---

## 비용 관리

- 1장으로 방향을 먼저 확인받는다
- 톤·팔레트가 확정되면 나머지를 일괄 생성한다
- 재생성은 실패한 장만 한다
- 생성 이력을 `state.json`에 남겨 중복 과금을 막는다

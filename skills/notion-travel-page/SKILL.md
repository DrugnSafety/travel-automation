---
name: notion-travel-page
description: 여행 일정을 Notion 가이드북으로 만드는 스킬. 메인 페이지, 날짜별 상세 페이지, 참고 자료 페이지(동물 도감·지질 이야기·체크리스트·긴급 정보·비용)를 구조적으로 생성하고, 한글 파손·하위 페이지 아카이빙·마크다운 이스케이프 같은 Notion 특유의 함정을 회피한다. 사용자가 노션에 여행 페이지 만들기, 여행 노션 정리, 노션 가이드북, 여행 페이지 수정, 노션 페이지 업데이트 등을 요청할 때 사용. Notion MCP 도구(fetch, notion-create-pages, notion-update-page, notion-create-file-upload)가 필요하다.
---

# Notion Travel Page

## 시작 전 필수

콘텐츠를 쓰기 전에 **반드시** 마크다운 명세를 읽는다. 문법을 추측하지 않는다.

```
fetch(id="notion://docs/enhanced-markdown-spec")
```

---

## 🚨 치명적 함정 4가지

과거 운영에서 실제로 전면 재작업을 유발한 것들이다.

### 함정 1 — 한글 파손

**증상**: 옥로스톤 → "열로스톤", 통나무집 → "통밥집", 진흘온첨 → "진흥온첨", 레인저 → "랑저", 벽난로 → "몸난로", 뇌우 → "되우"

**원인**: 콘텐츠를 유니코드 이스케이프(`\uXXXX`)로 조립해 넘김

**규칙**: **한글은 항상 문자 그대로 입력한다.** 이스케이프로 조립하지 않는다. 페이지 11개가 통찬에 파손된 사례가 있고, 자동 탐지가 어렵다(형태는 정상 한글이라 정규식에 안 걸린다).

**작성 후 검증**: `fetch`로 되읽어 고유명사(지명·시설명·외래어)를 원문과 대조한다.

---

### 함정 2 — 하위 페이지 아카이빙

**증상**: `Can't edit block that is archived. You must unarchive the block before editing.`

**원인**: 부모 페이지에 `replace_content` + `allow_deleting_content: true` 사용 → **새 본문에서 참조되지 않은 하위 페이지가 전부 아카이브됨**

**규칙**:
- 하위 페이지를 가진 페이지에는 `replace_content`를 쓰지 않는다. `update_content` 또는 `insert_content`를 쓔다.
- 부득이면 새 본문에 모든 하위 페이지의 `<page url="...">제목</page>` 링크를 포함시킨다.

**복구**: API로는 안 된다. `notion-move-pages`는 "already in the target location"만 반환한다. 사용자가 **노션 좌측 하단 휴지통 → 우클릭 → 복원**을 직접 해야 한다.

---

### 함정 3 — 마크다운 이스케이프

| 문자 | 표기 | 이유 |
|---|---|---|
| `~` | `\~` | 취소선 |
| `$` | `\$` | 수식 |

`8/16~17` → `8/16\~17`, `$260/박` → `\$260/박`

---

### 함정 4 — 아이콘에 이미지 URL

**증상**: `Invalid page icon URL`

**규칙**: **아이콘은 이모지, 커버는 외부 이미지 URL.**

```
icon: "🦬"
cover: "https://images.pexels.com/photos/{ID}/...&w=1600"
```

---

## 페이지 구조

### 메인 페이지

```markdown
> **{기간}** · {출발지} 출발 · {인원 구성} · {교통수단 요약}

![{대표 이미지}]({Pexels URL w=1280})

<image src="file-upload://{AI 일러스트 ID}">{여행명} 전체 여정</image>

---
## 🗺️ 한눈에 보기
<table header-row="true">
<tr><td>구간</td><td>일자</td><td>거점</td><td>차량</td><td>핵심</td></tr>
</table>

---
## ✈️ 항공·차량
## 폐️ 숙박 (예약 우선순위)
## 🌡️ 기후
## 📂 상세 페이지
## ⚠️ 이번 여행의 핵심 리스크
```

**핵심 리스크 절을 반드시 넣는다.** 시간이 촉박한 차량 교체, 마지막 날 비행기 시각 역산, 예약 미확정 구간, 통행 제약 같은 것들이다. 사용자가 가장 먼저 확인하는 부분이다.

### 날짜별 페이지

```markdown
<image src="file-upload://{일러스트 ID}">Day {N} — {구간}</image>

> **{날짜} ({요일})** · {거점} · 주행 {거리} / {시간}

## 📍 오늘의 개요
## ⏰ 타임라인
<table header-row="true">
<tr><td>시각</td><td>장소</td><td>소요</td><td>메모</td></tr>
</table>

## 🚗 이동 시간표

---
## {번호}. {스팟명}
![{대표}]({URL w=1280})
![{디테일}]({URL w=1280})

{2~3문장 개요}

<table header-row="true">
<tr><td>항목</td><td>정보</td></tr>
<tr><td>위치</td><td>...</td></tr>
<tr><td>소요 시간</td><td>...</td></tr>
<tr><td>난이도</td><td>...</td></tr>
</table>

> 🌍 **역사·유래**
> 👀 **관람 포인트**
> 🅿️ **주차**
> ⏰ **추천 시간대**
> 💡 **현지 팁**

---
## 🗺️ Day {N} 지도
(travel-maps-integration 이 삽입)
```

**스팟마다 5개 블록이 모두 있어야 한다**: 역사·유래 / 관람 포인트 / 주차 / 추천 시간대 / 현지 팁. 하나라도 빠지면 품질 게이트에서 걸린다.

### 참고 자료 페이지

여행 성격에 맞춰 만든다.

| 페이지 | 언제 |
|---|---|
| 🦌 동물 도감 (아이 교육용) | 자연·국립공원 + 아동 동반 |
| 🌋 지리·지질 이야기 | 화산·협곡·해안 지형 |
| 🏛️ 역사·인물 이야기 | 도시·유적 |
| ✅ 예약 체크리스트 | 항상 (D-day 역산) |
| 🎒 짐싸기 체크리스트 | 항상 |
| 🚨 긴급 정보·의료·안전 | 항상 |
| 💰 예상 비용 | 항상 |
| 🗺️ 전체 지도·경로 링크 | 지도 연동 시 |

아이 교육용 페이지는 **부모가 현장에서 읽어줄 수 있는 설명 스크립트**를 포함한다. 항목마다 사진을 넣는다.

---

## 생성 순서

```
1. 스캐폴드   — 메인 + 날짜별 + 참고 자료의 껵데기만 생성, 페이지 ID 즉시 기록
2. 본문       — 페이지별로 순차 작성 (replace_content 사용 가능. 하위 페이지 없는 페이지에 한함)
3. 이미지     — travel-image-search
4. 일러스트   — travel-illustration
5. 지도       — travel-maps-integration (insert_content)
6. 상호 링크  — 메인에서 하위로, 하위에서 메인으로 (update_content)
7. 검증       — travel-quality-loop
```

**메인 페이지 본문은 스캐폴드 직후에 한 번만 `replace_content`로 완성하고, 이후에는 `insert_content`/`update_content`만 쓴다.**

---

## 요일 표기

`trip-brief.json`의 `day_map`만 사용한다. **요일을 추론해서 쓰지 않는다.**

```bash
python3 -c "
import datetime
s=datetime.date(2026,8,14); W='월화수목금토일'
for i in range(11):
    d=s+datetime.timedelta(days=i); print(f'Day {i+1}: {d} ({W[d.weekday()]})')
"
```

---

## 자주 쓰는 Notion 마크다운

```markdown
<table header-row="true">
<tr><td>헤더1</td><td>헤더2</td></tr>
<tr><td>값1</td><td>값2</td></tr>
</table>

<embed src="{URL}">캐션</embed>

<image src="file-upload://{ID}">캐션</image>

<page url="{페이지 URL}">제목</page>          ← 페이지를 이동시킨다. 주의
<mention-page url="{페이지 URL}">제목</mention-page>   ← 인라인 참조. 안전

> 💡 **콜아웃 제목**
>
> 본문
```

> ⚠️ `<page url=...>`는 **해당 페이지를 현재 위치로 이동**시킨다. 단순 링크가 목적이면 `<mention-page>`를 쓴다.

---

## 오류 대응

| 오류 | 대응 |
|---|---|
| `No matches found` | `fetch`로 현재 본문 재확인 후 `old_str`을 더 짧고 고유하게 |
| `Invalid JSON: unexpected end of hex escape` | 콘텐츠가 너무 크거나 이스케이프 문제. **분할해서 여러 번 호출**
| `Invalid page icon URL` | 아이콘을 이모지로 |
| `Can't edit block that is archived` | 함정 2 참조. 사용자에게 휴지통 복원 요청 |
| 콘텐츠 누락 | 한 번에 넣는 양이 과함. 섹션별로 나눠 `insert_content` |

**큰 페이지는 한 번에 만들지 않는다.** 골격을 만들고 섹션별로 `insert_content`하는 편이 안정적이다.

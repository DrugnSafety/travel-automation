---
name: travel-notion-export
description: 노션에 생성된 여행 가이드북(메인 페이지 + Day별·교통·짐·긴급 서브페이지 전체)을 마크다운으로 변환해 GitHub 리포지토리에 커밋·푸시합니다. 사용자가 노션 페이지를 깃허브에 올려줘, 여행 가이드 백업, github에 push/commit, 마크다운으로 내보내기 등을 요청할 때 이 스킬을 사용하세요.
---

# Travel Notion Export

Notion으로 만든 여행 가이드북 페이지 트리를 로컬 마크다운 파일로 변환하고, Git 커밋을 거쳐 GitHub 리포지토리에 반영하는 스킬. **여행 데이터(가족·자녀 정보 포함)는 코드가 아니므로 플러그인 리포와 분리된 전용 리포에 저장**하는 것이 원칙이다.

## 0. 개인정보 원칙 (필수 확인)

CLAUDE.md IX.4에 따라 가족·자녀 개인정보는 공개 산출물에 노출할 수 없다. 실행 전 매번 확인한다:

1. 대상 리포가 **private**인지 확인한다. `gh repo view {owner}/{repo} --json visibility`로 확인, 미존재 시 `gh repo create {owner}/{repo} --private`로 생성한다. **public 리포에는 여행 데이터를 절대 push하지 않는다** — 사용자가 public을 명시적으로 요구해도, 자녀 이름·나이·학년·예약번호 등 식별 정보가 포함되어 있으면 익명화 여부를 먼저 확인 질문(AskUserQuestion)한다.
2. 플러그인 코드(스킬·커맨드)를 push하는 별도 작업과 혼동하지 않는다 — 코드는 `travel-automation` 등 별도 public 리포, 여행 데이터는 `travel-guides` 등 private 리포로 분리 유지한다.

## 1. 내보낼 페이지 트리 수집

1. 사용자가 준 노션 페이지 URL(허브 또는 개별 여행 메인 페이지)을 `fetch`한다.
2. 페이지 본문에서 링크된 서브페이지(Day N, 교통 정보, 짐 싸기, 긴급 정보 등)를 모두 추출한다. `notion-travel-page` 표준 구조상 서브페이지는 메인 페이지 본문에 1단계로만 링크되어 있다 — 재귀는 1단계면 충분하다.
3. 서브페이지가 데이터베이스(관광지 리서치 DB 등)인 경우 `notion-query-data-sources`로 전체 행을 조회하고, 각 행이 개별 페이지면 함께 수집 대상에 포함한다.
4. 여러 여행을 한 번에 내보낼 때(허브 페이지 전체)는 여행별로 폴더를 분리한다.

## 2. 마크다운 변환

각 노션 페이지를 다음 프런트매터 + 본문 형식으로 변환한다:

```markdown
---
title: "{페이지 제목}"
notion_url: "{원본 URL}"
exported_at: "{ISO 날짜}"
---

{fetch 결과의 <content> 내부를 마크다운으로 그대로 사용 — <page>, <properties> 등 래퍼 태그는 제거하고 순수 본문만 남긴다}
```

- 파일명: `{순번:02d}-{제목 슬러그}.md` (예: `00-메인.md`, `01-Day1-Antelope-Canyon.md`)
- 이미지가 Notion 첨부(`file-upload://`)인 경우 원본 URL이 만료될 수 있으므로, 가능하면 소스 URL(위키피디아·catbox 등)을 병기하고 `![alt]({url})`로 삽입한다.
- 여행별 폴더 구조 예:
  ```
  {여행_슬러그}/
    00-메인.md
    01-Day1-*.md
    02-Day2-*.md
    교통정보.md
    짐싸기.md
    긴급정보.md
  ```

## 3. Git 커밋 & 푸시

```bash
cd {로컬_export_경로}
git init -q 2>/dev/null  # 이미 초기화된 경우 무시
git add {여행_슬러그}/
git commit -m "{여행명} 가이드북 내보내기 ({날짜})"
git remote get-url origin 2>/dev/null || git remote add origin https://github.com/{owner}/{repo}.git
git push -u origin main
```

- 원격 리포가 없으면 1단계에서 확인한 대로 **private**로 먼저 생성한다: `gh repo create {owner}/{repo} --private --source=. --remote=origin`
- 이미 내보낸 여행을 다시 내보낼 때는 동일 폴더를 덮어쓰고 diff가 있는 파일만 커밋에 포함된다(정상 동작).
- 커밋 메시지에는 개인정보(자녀 실명 등)를 넣지 않는다 — 여행명·날짜만 사용.

## 4. 결과 보고

푸시 완료 후 사용자에게 리포 URL과 내보낸 여행 목록(폴더명)만 한 줄로 보고한다. 상세 파일 목록 나열은 생략한다.

## 파이프라인 내 위치

독립 실행 스킬 — 오케스트레이터 파이프라인에는 포함하지 않는다(여행 완성 후 사용자가 필요할 때 명시적으로 호출). `notion-travel-page`로 가이드북이 완성된 이후 아무 때나 실행 가능.

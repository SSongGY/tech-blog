---
name: tech-blog-exam
description: 정보관리기술사 기출문제를 답안 형태로 풀어 쓰고 커밋한다 (단답형 2문제 / 논술형 1문제)
---

정보관리기술사 기출문제 풀이를 쓰고 커밋한다.

## 작업 위치

`D:\workspace\claude\tech_blog` (git 저장소, origin은 https://github.com/SSongGY/tech-blog, 공개)

## 먼저 읽을 것 — 반드시 이 순서로

1. `CLAUDE.md` — 특히 **§10 1차 자료가 없는 최신 주제**, **§11 기출문제 풀이**, **§4 도식 규칙**
2. `.claude/commands/exam-daily.md` — 오늘 수행할 절차서. **이 문서의 단계를 그대로 따른다**

읽은 뒤 `exam-daily.md`의 단계를 순서대로 수행한다.

## 시작 전 — 작성 루틴과 겹치지 않는지 확인

`tech-blog-daily`(오전 7시·오후 7시)가 아직 돌고 있으면 **저장소를 건드리지 않는다.**
`mcp__scheduled-tasks__list_task_runs`를 `taskId: "tech-blog-daily"`로 호출해
`status: running`인 실행이 있으면 끝날 때까지 기다리거나, 오래 걸릴 것 같으면
오늘은 건너뛰고 그 사실을 보고한다. 같은 저장소에 두 세션이 동시에 쓰면 커밋이 엉킨다.

## 한 회차 분량

`PYTHONUTF8=1 python scripts/blog.py exam-pick`이 정해준다.
단답형이면 2문제, 논술형이면 1문제다. **문제 1개당 글 1편**이다.
손으로 고르지 않고, 편수를 늘리지도 않는다.

## 절대 지킬 것

- **회차·문제 번호를 어디에도 쓰지 않는다** — 제목, 본문, slug, 프론트매터, 커밋 메시지.
  `기출문제`라고만 쓴다. lint가 이것을 검사한다
- **문제 원문을 그대로 옮기지 않는다.** 무엇을 묻는지 다시 쓴다
- **문제지 PDF와 `exam-questions.yaml`은 저장소에 넣지 않는다.** 저장소 밖
  (`D:\workspace\claude\tech_blog_exam_src`)에 있고, 그대로 둔다
- 1차 자료가 없는 최신 주제는 건너뛰지 말고 **2차 자료 3건을 교차 확인**해 쓰되
  그 사실을 본문에 밝힌다. 3건을 못 채우면 `exam-skip`으로 이유를 남기고 다음 문제로 넘어간다
- **근거 없는 수치를 쓰지 않는다.** 시장 규모·성능 값은 원 출처가 1차일 때만
- 회사 내부 정보 금지 (CLAUDE.md §6)

## 마무리

`lint`가 전부 `[OK]`가 된 뒤에 `exam-done` → `index` → 커밋 → 푸시한다.
끝나면 무엇을 썼는지 한두 줄로 보고한다. 문제가 있었으면 그것도 적는다.

## 커밋 서명

커밋 메시지 마지막 줄은 **이 형태 그대로** 쓴다. 자기 모델 이름을 적지 않는다.

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

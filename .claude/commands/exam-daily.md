---
description: 정보관리기술사 기출문제를 풀어 답안 형태로 쓰고 커밋한다
---

오늘치 기출문제 풀이를 쓴다. 개념 정리(`pe` 트랙)와 **다르다.** 여기서는
**답안지에 그대로 옮겨 쓸 수 있는 형태**로 쓴다.

## 먼저 읽을 것

1. `CLAUDE.md` **§11 기출문제 풀이** — 답안 구조, 표기 금지 규칙
2. `CLAUDE.md` **§10 1차 자료가 없는 최신 주제** — 출처 등급. 최신 주제에서 반드시 쓴다
3. `CLAUDE.md` **§4 도식 규칙** — SVG 작성과 출처 표기

## 1. 문제 고르기

```bash
PYTHONUTF8=1 python scripts/blog.py exam-pick
```

단답형이면 **2문제**, 논술형이면 **1문제**가 나온다. 손으로 고르지 않는다.
**문제 1개당 글 1편**이다. 단답형 2문제면 글도 2편이다.

## 2. 조사 — 출처 등급을 먼저 정한다

문제마다 1차 자료부터 찾는다. **영문 원어·표준화 기구·제안 기업 이름으로 각각 검색한다.**
한글 용어만 검색하고 "자료 없음"으로 판단하지 않는다.

- **1차 자료가 있다** → 그것으로 쓴다. 2차는 보조로만
- **1차 자료가 없다** → 독립된 출처 **3건 이상**을 교차 확인한다.
  같은 원문을 옮긴 글들은 하나로 센다. 발행일을 함께 기록한다
- **3건을 못 채운다** → 쓰지 않는다:

  ```bash
  PYTHONUTF8=1 python scripts/blog.py exam-skip <id> --reason "왜 못 썼는지"
  ```

  건너뛴 뒤 `exam-pick`을 다시 돌려 다음 문제를 받는다.

### 받아온 자료를 읽을 때

`WebFetch`가 받은 PDF·텍스트는 **저장소 밖**에 떨어진다. 그 폴더로 `cd` 하지 말고
**저장소 루트에 선 채 절대경로로** 읽는다. `cd`로 작업 폴더를 벗어나면 권한을 묻느라
무인 실행이 멈춘다.

```bash
# 이렇게 — 명령이 grep/sed/python 으로 시작한다
grep -n -i "phase" "C:/Users/song/.claude/projects/.../tool-results/atam.txt"

# 이렇게 하지 않는다 — cd 로 작업 폴더를 벗어난다
cd "C:/Users/song/.claude/projects/.../tool-results" && grep -n -i "phase" atam.txt
```

웹 요청은 `curl` 대신 `WebFetch`·`WebSearch`를 쓴다.

## 3. 글 만들기

```bash
mkdir -p posts/PE/exam/$(date +%Y-%m-%d)-<slug>/fig
```

`<slug>`는 주제의 영문 소문자다. **회차·번호를 slug에 넣지 않는다.**

프론트매터:

```yaml
---
title: "기출문제 — <주제>"
date: <오늘>
categories: [PE]
subcategory: exam
track: exam
exam_kind: short          # short(단답형) | essay(논술형)
tags: [정보관리기술사, 기출문제, <주제 태그>]
description: "한 줄 요약"
difficulty: 중급
environment: ["<근거 문서와 판/연도>"]   # 예: "ISO/IEC 25010:2011"
verification: manual-only
verified: true
---
```

`environment`에는 **답안의 근거가 된 문서를 판·연도까지** 적는다. lint가 숫자 포함을 검사한다.
`manual-only`이므로 본문에 **"실행 검증 없음"** 문구가 들어가야 한다. 계산 문제를 직접
검산했다면 `executed`로 올리고 계산 과정을 싣는다.

1차 자료가 없어 2차로 썼다면 본문 상단에 밝힌다:

```markdown
> 1차 자료 없음. 2차 자료 3건을 교차 확인해 정리했다. (§10)
```

## 4. 답안 쓰기

§11의 구조를 그대로 따른다.

- 단답형: `Ⅰ. 정의` → `Ⅱ. 구성요소` → `Ⅲ. 활용/고려사항`. 모식도 1개
- 논술형: `Ⅰ. 개요` → 문항이 물은 항목 순서 그대로 → `Ⅴ. 결론`. 모식도 1개 + 비교표 1개
- **문항이 "가. 나. 다."로 나눠 물으면 그 순서를 바꾸지 않는다**
- 마지막 줄은 `끝`
- 답안 뒤에 `## 답안 작성 메모` — 무엇부터 쓸지, 시간이 모자라면 무엇을 버릴지,
  점수가 갈리는 지점은 어디인지

도식은 `fig/`에 SVG로 두고 바로 아래에 근거를 적는다:

```markdown
![설명](fig/이름.svg)

> **출처**: [문서 제목 §절](URL)
```

2차 자료만으로 그렸으면 근거 줄 끝에 `(2차 자료 기반)`을 붙이고, 내부 구조나
프로토콜 흐름은 그리지 않는다. 개념 관계도까지만이다.

**작성 후 브라우저로 열어 글자 잘림·겹침을 확인한다.**

## 4-1. 블로그에 없는 개념은 백로그로 넘긴다

답안을 쓰다 보면 블로그에 아직 정리되지 않은 개념이 나온다. **답안 안에서 개념을
길게 풀지 않는다.** 답안은 답안대로 끝내고, 개념은 등록만 해둔다.

```bash
PYTHONUTF8=1 python scripts/blog.py add-topic \
  --track pe --title "<개념 이름>" --subcategory <분야> \
  --tags "정보관리기술사,<분야>,개념정리" \
  --angle "<어느 각도로 쓸지>" --origin exam
```

**오후 5시 개념 루틴**이 `--origin exam`으로 등록된 것을 먼저 가져간다.
**여기서 개념 글까지 쓰지 않는다.**
이미 백로그에 있거나 발행된 주제면 명령이 알아서 걸러내므로 중복은 걱정하지 않아도 된다.

개념 글이 **이미 있으면** 답안 끝(`끝` 위)에 링크 한 줄을 넣는다.

```markdown
> 개념 정리: [제목](../../software-engineering/2026-09-18-<slug>/index.md)
```

있는지 확인은 `POSTS.md`를 보면 된다.

```bash
grep -i "<개념 영문/한글>" POSTS.md
```

## 5. 검사

```bash
PYTHONUTF8=1 python scripts/blog.py lint
```

`[NG]`가 하나라도 있으면 고친 뒤 다시 돌린다. lint는 회차·번호가 새어 나갔는지도 검사한다.

## 6. 마무리

```bash
PYTHONUTF8=1 python scripts/blog.py exam-done <id> [<id>...]
PYTHONUTF8=1 python scripts/blog.py index
git add -A
git commit -F - <<'MSG'
exam: <주제>

{본문 — 무엇을 왜 바꿨는지}

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
git push
```

커밋 메시지에도 **회차·번호를 쓰지 않는다.**

## 하지 말 것

- **회차·문제 번호를 어디에도 쓰지 않는다** — 제목, 본문, slug, 프론트매터, 커밋 메시지
- **문제 원문을 그대로 옮기지 않는다.** 무엇을 묻는지 내 문장으로 다시 쓴다
- **문제지 PDF와 `exam-questions.yaml`을 저장소에 넣지 않는다.** 저장소 밖에 있다
- 근거 없는 수치·시장 규모·성능 값 금지. 원 출처가 1차일 때만 쓴다
- 근거가 모자라면 억지로 쓰지 말고 `exam-skip`으로 이유를 남긴다
- `tech-blog-daily` 회차가 돌고 있으면 **저장소를 건드리지 않는다.** 끝난 뒤에 시작한다

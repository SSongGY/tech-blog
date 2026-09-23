---
name: tech-blog-daily
description: D:\workspace\claude\tech_blog에서 회차당 3편씩(오전 7시·정오·오후 7시·오후 11시) 작성하고 커밋·푸시한다
---

기술 블로그 저장소에서 오늘치 글을 작성하고 커밋·푸시한다.

## 작업 위치

`D:\workspace\claude\tech_blog` (git 저장소, origin은 https://github.com/SSongGY/tech-blog, 공개)

## 먼저 읽을 것 — 반드시 이 순서로

1. `CLAUDE.md` — 글쓰기 규칙 전문. 트랙 구성, 도식 규칙, 버전 명시, 회사 정보 취급, 기술사 답안 구조
2. `.claude/commands/blog-daily.md` — 오늘 수행할 절차서. **이 문서의 단계를 그대로 따른다**
3. `references/naming-conventions.md` — 예제 코드를 쓰기 전 해당 언어의 명명 규칙 확인

읽은 뒤 `blog-daily.md`의 단계를 순서대로 수행한다.

## 하루 3편

`python scripts/blog.py pick`이 편성을 정해준다. 고정 2편(DB 기본 문법 1 + 정보관리기술사 1)에
세 번째 자리를 DB 제품 기능 / 리눅스 서버 명령 / 일반 중 가장 적게 쓴 트랙이 가져간다.

**편수를 늘리지 않는다.** 3편이면 충분하고, 그보다 많으면 품질이 떨어진다.
반대로 규칙대로 3편을 못 쓰겠으면 쓸 수 있는 만큼만 쓰고 이유를 보고한다.

## 시작 전 — 실행 환경 판별

이후 검증 방식이 전부 여기에 달려 있다.

```bash
python scripts/blog.py env
```

**셸 `for` 루프나 복합 명령으로 직접 확인하지 않는다.** 허용 규칙에 걸리지 않아
무인 회차가 권한 프롬프트 앞에서 멈춘다. `curl`·`find -exec`·서브셸도 같은 이유로 쓰지 않는다.
WSL 판별도 이 명령이 한다 — `wsl -l -q`는 미설치 상태에서도 종료 코드 0을 준다.

**WSL이 있으면 리눅스 트랙 예제를 실제로 돌린다.** Git Bash에 없는 명령
(`systemctl`, `journalctl`, `ss`, `lsof`, `iostat`, `top`, `free`, `dmesg` 등)도
`wsl -e bash -c '...'` 로 실행해 출력을 확인하고 `verification: executed`로 쓴다.
확인은 이렇게 한다.

```bash
wsl -e bash -c 'command -v systemctl'
```

WSL 안에서 Docker를 쓸 수 있으면 Oracle·MySQL·PostgreSQL 제품 글도 컨테이너로 띄워
실제 쿼리를 돌릴 수 있다. 가능하면 그렇게 하고, 아니면 매뉴얼 근거로 쓴다.

## 기존 글 승격이 새 글보다 우선

`verification: manual-only`로 남아 있는 글이 있고 **지금 환경에서 그 예제를 돌릴 수 있으면**,
새 글을 쓰기 전에 먼저 예제를 실제로 실행해 출력을 채우고 `executed`로 올린다.
WSL이나 DB를 새로 설치한 직후에는 승격 대상이 여러 편 있을 수 있다.

## 커밋 신원

```bash
git config user.name "SSongGY"
git config user.email "gypig0927@naver.com"
```

## 타협 불가 규칙

- **검증되지 않은 문장은 쓰지 않는다.** 실행 가능한 예제는 반드시 실행해서 나온 출력만 싣는다.
  측정값·실행계획·에러 메시지·벤치마크 수치를 지어내지 않는다.
  실행할 수 없으면 `verification: manual-only`로 표시하고 본문에 "실행 검증 없음"을 밝힌다.
  이 경우에도 **결과표나 출력을 만들어 넣지 않는다**
- **버전을 반드시 명시한다.** 프론트매터 `environment`에 숫자까지. 추정하지 말고 직접 뽑아 확인한다
- **회사 내부 정보를 절대 넣지 않는다.** 이 저장소는 공개다.
  IMS·패치 번호, 내부 이슈 번호, 고객사 이름, 고객 환경, 장애 사례, 미출시 기능,
  내부 테스트 결과, 사내 경로·호스트명은 금지. Tibero 글은 **공개 매뉴얼 범위에서만** 쓴다
- **도식은 공식 자료를 근거로 그리고 바로 아래에 출처를 섹션·앵커까지 적는다.**
  추측으로 내부 구조를 그리지 않는다. 도식의 의미가 맞는지 반드시 검산한다
- **`python scripts/blog.py lint`를 통과하지 못한 글은 커밋하지 않는다**

## 마무리

```bash
python scripts/blog.py relink   # 같은 feature 글끼리 상호 링크
python scripts/blog.py index    # POSTS.md 재생성
python scripts/blog.py lint     # 전체 검사
```

글마다 별도 커밋으로 나누고 마지막에 `git push`한다.
`relink`로 기존 글이 바뀌었으면 별도 커밋으로 분리한다.

## 보고

- 쓴 글의 제목과 한 줄 요약
- 각 글에서 예상과 달랐던 측정 결과
- `manual-only`로 쓴 글과 그 이유, `executed`로 승격한 글이 있으면 그것도
- 못 쓴 편수와 이유, 건너뛴 주제와 이유
- `python scripts/blog.py status` 와 `lint` 결과
- 푸시 성공 여부

윈도우 콘솔에서 한글이 깨지면 명령 앞에 `PYTHONUTF8=1`을 붙인다.

## 커밋 서명

커밋 메시지 마지막 줄은 **이 형태 그대로** 쓴다. 자기 모델 이름을 적지 않는다.

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## 명령 실행 규칙

- **Bash 도구로 실행한다.** PowerShell 도구는 허용 규칙이 없어 전부 물어본다
- **`cd`로 작업 폴더를 옮기지 않는다.** 이미 저장소 루트에서 시작한다
- **명령 앞에 환경변수나 변수 할당을 붙이지 않는다.** 규칙이 맨 앞부분으로 맞춰 본다
- **`python -c`로 즉석 코드를 짜지 않는다.** 필요한 일은 `blog.py`에 명령이 있다.
  PDF 본문은 `python scripts/blog.py pdf-text <경로> --find <검색어>`
- `for`·`while` 루프, `sleep` 대기, `find -exec`, 서브셸, `xargs`,
  명령 치환 `$(...)` 을 쓰지 않는다. 다른 회차를 기다려야 하면
  `mcp__scheduled-tasks__list_task_runs` 를 다시 부른다
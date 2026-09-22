# 다른 PC에서 이어받기

이 저장소는 **글과 규칙과 자동화가 한 벌**로 움직인다. 새 PC에서 이어받을 때
저장소만 클론하면 글은 보이지만 **루틴이 돌지 않는다.** 저장소에 들어오지 않는 것이
세 가지 있기 때문이다.

| 들어오지 않는 것 | 어디 있나 | 왜 |
|---|---|---|
| 권한 설정 | `.claude/settings.json` | 머신에 묶인 설정. gitignore 대상 |
| 스케줄 작업 | `~/.claude/scheduled-tasks/` | Claude Code가 머신별로 보관 |
| 기출문제 데이터 | 저장소 옆 `tech_blog_exam_src/` | 공공누리가 제140회부터만 적용된다 |

아래 순서대로 하면 된다. 1~4까지만 해도 손으로 쓰는 것은 다 된다.
5번부터가 자동 실행이다.

## 1. 클론과 커밋 identity

```bash
git clone https://github.com/SSongGY/tech-blog.git
cd tech-blog
git config user.name  "SSongGY"
git config user.email "gypig0927@naver.com"
```

회사 PC라면 전역 설정에 회사 메일이 잡혀 있을 수 있다. **저장소 단위로 지정**해야
개인 메일로 커밋된다.

## 2. 파이썬

```bash
python --version        # 3.13 이상에서 확인했다
pip install -r requirements.txt
```

`rlPyCairo`가 빠지면 티스토리용 PNG 변환만 실패한다. 글쓰기 자체는 영향 없다.

## 3. 잘 돌아가는지 확인

```bash
python scripts/blog.py status    # 백로그 잔량
python scripts/blog.py lint      # 기존 글이 전부 [OK] 여야 한다
```

`blog.py`가 시작할 때 출력 인코딩을 스스로 맞추므로(`sys.stdout.reconfigure`)
윈도우에서도 `PYTHONUTF8=1` 없이 한글이 나온다. 앞에 붙이지 않는다 —
환경변수를 붙이면 셸에 따라 문법이 갈리고(`VAR=1 cmd` 대 `$env:VAR=1; cmd`),
무인 회차가 허용 규칙에 걸리지 않아 멈춘다.

## 4. Claude에게 규칙 읽히기

**따로 할 일이 없다.** `CLAUDE.md`가 저장소에 있으므로 이 폴더에서 Claude Code를 열면
자동으로 읽는다. 절차서 `.claude/commands/*.md`도 슬래시 명령으로 바로 잡힌다.

| 읽는 것 | 무엇이 들어 있나 |
|---|---|
| `CLAUDE.md` | 글쓰기 규칙 전부 — 트랙, 톤, 도식, 출처 등급, 기출 답안 형식 |
| `.claude/commands/blog-daily.md` | 7시·19시 회차 절차 |
| `.claude/commands/exam-daily.md` | 15시 기출 답안 절차 |
| `.claude/commands/concept-daily.md` | 17시 개념 정리 절차 |
| `references/naming-conventions.md` | 언어별 변수명 규칙 |
| `OPERATIONS.md` | 운영 전반 — 구조, 명령어, 발행 절차 |

## 5. 권한 설정 — 이게 없으면 루틴이 멈춘다

```bash
cp .claude/settings.example.json .claude/settings.json
```

`settings.json`은 gitignore 대상이라 **복사는 새 PC마다 직접 해야 한다.**
자동 실행 루틴이 `git add -A`를 쓰기 때문에, 막아 두지 않으면 머신 설정이 저장소에
딸려 올라간다.

핵심은 `"defaultMode": "auto"` 한 줄이다. 이게 `acceptEdits`면 **파일 편집만**
자동 수락되고 Bash·MCP 호출은 여전히 물어봐서, 무인 회차가 프롬프트 앞에서 멈춘다.

경로가 다른 PC라면 `allow`의 경로성 규칙을 새 경로로 고친다.

## 6. 스케줄 작업 등록

`automation/scheduled-tasks/README.md`에 네 개의 작업과 등록 방법이 있다.
작업 프롬프트에 **절대경로가 박혀 있으니 새 PC 경로로 바꿔서** 등록한다.

```
07:00  tech-blog-daily       3편
15:00  tech-blog-exam        기출 답안 (단답형 2 / 논술형 1)
17:00  tech-blog-concept     개념 정리 2편
19:00  tech-blog-daily       3편
09:00  tech-blog-healthcheck 점검만
```

등록한 뒤 **한 번씩 수동 실행해 본다.** 권한을 묻는지 확인하는 것이 목적이다.
점검 루틴이 가장 짧고 저장소를 고치지 않으므로 그것부터 돌린다.
제대로 설정됐으면 1분 안에 끝난다.

## 7. 기출문제 데이터 (선택)

15시·17시 루틴을 쓸 때만 필요하다. 저장소 **바깥**에 둔다.

```
tech_blog_exam_src/
├─ 126.pdf ~ 140.pdf        문제지 원본
└─ exam-questions.yaml      추출한 465문제 + 진행 상태
```

기본 경로는 저장소 옆 `../tech_blog_exam_src`이고, `EXAM_SRC_DIR` 환경변수로 바꿀 수 있다.

**이 폴더를 저장소에 넣지 않는다.** 공공누리(KOGL)는 제140회부터 적용되므로 그 이전
회차의 문제 원문을 공개 저장소에 올릴 수 없다. 옮길 때는 USB나 개인 드라이브로
직접 복사한다.

```bash
python scripts/blog.py exam-status   # 잘 잡혔는지 확인
```

## 8. Tibero 실행 검증 (선택)

제품 트랙 글을 `executed`로 쓰려면 Tibero에 SSH로 붙어야 한다. 없으면 그 글들은
`manual-only`로 나가고, 그래도 규칙상 문제가 없다.

접속 정보는 **저장소에 넣지 않는다.** 키 등록은 직접 한다.

## 옮긴 뒤 확인할 것

```bash
python scripts/blog.py lint        # 전부 [OK]
python scripts/blog.py status      # 트랙별 잔량
python scripts/blog.py exam-status # 7번을 했다면
git log --oneline -5
```

점검 루틴을 수동으로 한 번 돌려 보고, 한 줄 보고가 나오면 이어받기가 끝난 것이다.

# 운영 가이드

IT 기술 글을 매일 **9~10편** 작성해 마크다운 원본과 실행 가능한 예제 코드를 함께 보관한다.
## 문서 안내

| 문서 | 무엇이 있나 |
|---|---|
| [POSTS.md](POSTS.md) | 작성한 글 목록 |
| [SETUP.md](SETUP.md) | **다른 PC에서 이어받는 절차** |
| [CLAUDE.md](CLAUDE.md) | 글쓰기 규칙 전문 — 트랙·톤·도식·출처 등급·기출 답안 형식 |
| [references/naming-conventions.md](references/naming-conventions.md) | 언어별 변수명 규칙 |
| [automation/scheduled-tasks/](automation/scheduled-tasks/) | 스케줄 작업 원본과 등록법 |
| 이 문서 | 구조·명령어·하루 흐름·발행 절차 |

```bash
pip install -r requirements.txt
python scripts/blog.py status   # 백로그 잔량
python scripts/blog.py lint     # 글 규칙 검사
```


| 시각 | 루틴 | 편수 | 내용 |
|---|---|---|---|
| 07:00 | `tech-blog-daily` | 3편 | 아래 트랙 구성 |
| 15:00 | `tech-blog-exam` | 단답형 2 / 논술형 1 | 기출 답안 |
| 17:00 | `tech-blog-concept` | 2편 | 15시 답안에서 나온 개념을 `pe` 글로 |
| 21:00 | `tech-blog-daily` | 3편 | 아래 트랙 구성 |
| 09:00 | `tech-blog-healthcheck` | — | 점검만. 저장소 수정 금지 |

07:00·21:00 회차의 트랙 구성은 다음과 같다.

| 트랙 | 편수 | 내용 |
|---|---|---|
| **DB 문법** `basics` | 1편 고정 | DB 기본 문법. SQLite로 재현 가능한 표준 SQL |
| **기술사** `pe` | 1편 고정 | 정보관리기술사 시험 과목 기술 개념·정의 |
| **DB 기능** `product` | 세 자리를 | DB 제품의 기능별 사용법·문법 |
| **리눅스** `linux` | 돌아가며 | 서버 운영에서 실제로 치는 명령 |
| **일반** `general` | 1편 | 그 외 IT 기술 |

세 번째 자리는 `product` / `linux` / `general` 중 가장 적게 쓴 트랙이 가져간다.
한 트랙이 소진돼도 나머지가 메우므로 편수는 줄지 않는다.

제품 트랙은 한 제품을 끝내면 다음으로 넘어간다 —
**Tibero 7 → Oracle 19c → MySQL 8.0 → PostgreSQL 16**. 같은 `feature` 키를 쓰므로
제품 간 비교 글이 자동으로 이어진다.

편수를 채우려고 기준을 낮추지 않는다. 규칙대로 못 쓰겠으면 쓸 수 있는 만큼만 쓰고 이유를 남긴다.

## 왜 git이 원본인가

티스토리와 네이버 블로그는 **API를 통한 글 발행이 불가능하다.**

- 티스토리 Open API: 2023년 12월 ~ 2024년 2월 순차 종료 (글 작성·수정·첨부 전부)
- 네이버 블로그 글쓰기 API: 2020년 5월 종료

따라서 이 저장소를 단일 원본(SSOT)으로 두고, 플랫폼 발행은 변환본을 붙여넣는 방식으로 한다.
나중에 GitHub Pages를 붙이면 그쪽은 push만으로 자동 배포된다.

## 구조

```
.
├─ CLAUDE.md                    글쓰기 규칙 (톤, 구조, 코드·도식 규칙)
├─ references/
│  └─ naming-conventions.md     언어별 공식 명명 규칙 — 예제 작성 전 확인
├─ topics/
│  ├─ backlog.yaml              주제 백로그 (status: todo/writing/done)
│  └─ published.md              발행 이력 — 중복 확인용
├─ posts/
│  └─ <카테고리>/[<제품·도구>/]YYYY-MM-DD-<slug>/
│     ├─ index.md               본문 (Jekyll/Hugo 호환 프론트매터)
│     ├─ fig/                   도식 SVG (공식 문서 근거 + 출처 표기 필수)
│     └─ code/                  실행 가능한 예제 소스 + README
├─ dist/tistory/                티스토리 붙여넣기용 변환본 (git 추적 제외)
├─ automation/scheduled-tasks/  스케줄 작업 4개의 원본 사본 + 등록법
├─ .claude/
│  ├─ commands/*.md             회차별 절차서 (슬래시 명령)
│  └─ settings.example.json     권한 설정 템플릿 (실제 settings.json 은 gitignore)
├─ SETUP.md                     다른 PC에서 이어받는 절차
├─ requirements.txt             파이썬 의존성 (실제로 돌려 본 버전)
└─ scripts/blog.py              운영 CLI
```

저장소 **바깥**에 있는 것이 둘 있다. `SETUP.md`를 본다.

- `.claude/settings.json` — 권한 설정. 머신에 묶여 있다
- `../tech_blog_exam_src/` — 기출문제 PDF와 465문제 데이터. 공공누리가 140회부터만 적용된다

## 글 분류

글은 **분야별 폴더**에 들어간다. 경로는 백로그의 `category`와 `subcategory`로 결정된다.

```
posts/
├─ Database/
│  ├─ sql-basics/   ← DB 기본 문법 (track: basics)
│  ├─ tibero/       ← 제품 시리즈 1순위
│  ├─ oracle/       ← 제품 시리즈 2순위
│  ├─ sqlite/2026-09-18-btree-index-not-used/
│  └─ mariadb/
├─ PE/              ← 정보관리기술사 (track: pe)
│  ├─ software-engineering/, database/, network/, security/
│  └─ system/, emerging-tech/, it-management/
├─ Backend/
│  └─ redis/
├─ Tooling/
│  └─ git/2026-09-18-git-bisect-run-automation/
├─ Language/ (python, go, rust, javascript)
├─ Infra/    (linux, docker, kubernetes, tls)
├─ Performance/, Architecture/, Security/
```

카테고리 8종은 `blog.py`의 `CORE_CATEGORIES` 기준으로 core/general이 갈린다.
`subcategory`는 **특정 제품·도구에 묶인 주제에만** 붙인다. 벤더 중립 주제
(예: MVCC 일반론, CAP 정리)는 비워 두면 카테고리 폴더 바로 아래에 들어간다.

## 제품 간 기능 비교

프론트매터 `feature` 키가 제품을 넘어 같은 기능을 잇는다. 예를 들어 `transaction-isolation`을
Tibero 7과 SQLite에서 각각 쓰면, 두 글이 서로를 가리키고 비교 절이 들어간다.

```bash
python scripts/blog.py related transaction-isolation   # 같은 기능으로 쓴 글 확인
python scripts/blog.py relink                          # 상호 링크 블록 재생성
```

`relink`가 만드는 블록은 손으로 고치지 않는다. 새 글이 추가되면 **기존 글에도 역링크가
자동으로 생기므로** 그 글들도 함께 커밋해야 한다.

```markdown
<!-- related:start -->
> **같은 기능을 다른 환경에서 다룬 글** (`transaction-isolation`)
> - [제목](../../sqlite/2026-09-20-.../index.md) — SQLite 3.49.1
<!-- related:end -->
```

현재 제품·일반 양쪽에 짝이 맞는 `feature`는 다섯 개다 — `explain-plan`, `optimizer-hint`,
`row-limiting`, `table-partitioning`, `transaction-isolation`.

## 쓴 글 보기

루트의 **[POSTS.md](POSTS.md)** 가 글 목록이다. 트랙별로 묶여 있고 제목을 누르면 바로 열린다.
날짜·난이도·환경(버전)·검증 방식이 한눈에 보이고, 같은 기능을 여러 환경에서 다룬 글도 묶여 있다.

`python scripts/blog.py index`로 다시 만든다. 직접 고치지 않는다.

## 사용법

```bash
python scripts/blog.py status                 # 트랙별 잔량, 비율, 미검증·미실행 글
python scripts/blog.py pick                   # 이번 회차에 쓸 주제 3편 선정
python scripts/blog.py pick --general 6       # 일반 주제를 더 받아 실행 가능한 것 고르기
python scripts/blog.py pick-concepts          # 17시용 pe 주제 2편 (기출발 우선)
python scripts/blog.py add-topic --track pe … # 백로그에 주제 추가 (--origin exam)
python scripts/blog.py exam-pick              # 다음에 풀 기출문제
python scripts/blog.py exam-done <id> …       # 기출 풀이 완료 처리
python scripts/blog.py exam-skip <id> --reason "…"   # 근거 부족으로 건너뜀
python scripts/blog.py exam-status            # 기출 진행 현황
python scripts/blog.py tasks-diff             # 스케줄 작업 사본이 실제와 같은지 대조
python scripts/check_stuck.py                 # 멈춘 회차 찾기 (손으로 확인할 때)
python scripts/blog.py env                    # 실행 환경 판별 (버전·DB 클라이언트·리눅스 도구)
python scripts/blog.py recent 6,24            # 최근 수정된 글과 크기
python scripts/blog.py check-svg              # 도식 기계 검사 (폭·배경·글자·넘침)
python scripts/blog.py check-links            # 인용 링크와 앵커가 살아 있는지
python scripts/blog.py pdf-text <파일> --find BM25   # PDF 본문을 쪽 단위로 (조사용)
python scripts/blog.py run-example <글 폴더>  # 예제를 돌려 code/output.txt 에 기록
python scripts/blog.py run-examples           # executed 글의 예제를 전부 다시 돌린다
python scripts/blog.py new tb-001 my-slug     # 글 폴더 스캐폴딩 (fig/, code/ 포함)
python scripts/blog.py related sequence       # 같은 기능으로 쓴 글 찾기
python scripts/blog.py relink                 # 같은 기능 글끼리 상호 링크 재생성
python scripts/blog.py lint                   # 글 규칙 검사
python scripts/blog.py index                  # 글 목록 페이지(POSTS.md) 재생성
python scripts/blog.py done tb-001            # 발행 완료 처리 + 이력 기록
python scripts/blog.py tistory my-slug        # 티스토리용 변환 (도식은 PNG로 구워짐)
```

도식을 그린 뒤에는 브라우저로 직접 열어 글자 잘림·겹침을 확인한다.

```bash
python -m http.server 8771 --bind 127.0.0.1
```

`blog.py`가 출력 인코딩을 스스로 맞추므로 윈도우에서도 환경변수 없이 한글이 나온다.
**`PYTHONUTF8=1`을 앞에 붙이지 않는다** — 셸마다 문법이 달라(`VAR=1 cmd` 대
`$env:VAR=1; cmd`) 무인 회차가 허용 규칙에 걸리지 않아 멈춘다.

## 하루 작업 흐름

0. 실행 환경을 확인한다 (`command -v tbsql` 등). 이후 검증 방식이 여기에 달려 있다
1. `pick`으로 이번 회차 3편을 받는다. 같은 기능으로 쓴 글이 있으면 함께 표시된다
2. `new`로 폴더를 만든다
3. 예제를 작성한다
   - 일반 트랙: **실제로 실행해 출력을 확인한다** (`verification: executed`)
   - 제품 트랙에 실행 환경이 없으면: 공식 매뉴얼 근거로 쓰고 `manual-only`로 표시.
     **출력을 지어내지 않는다**
4. 공식 문서를 근거로 `fig/`에 SVG 도식을 그리고, **도식 아래에 `> **출처**:` 줄을 남긴다**
5. **버전을 직접 뽑아 `environment`에 숫자까지 적는다**
6. 같은 기능의 글이 있으면 `## 다른 환경에서는` 절로 비교한다
7. `relink`로 상호 링크를 만든다 (기존 글에도 역링크가 생긴다)
8. `verified: true`로 바꾸고 `lint`를 통과시킨다
9. `done`으로 이력에 기록하고 글마다 별도 커밋으로 나눠 커밋·푸시한다
10. `tistory`로 변환본을 뽑아 에디터에 붙여넣고 발행한다 (도식 SVG는 따로 업로드)

`manual-only` 글은 나중에 그 제품이 있는 환경에서 `/blog-daily`를 돌리면 예제를 실제로 돌려
출력을 채우고 `executed`로 승격한다. 새 글보다 이 승격이 우선이다.

## 티스토리·네이버 발행

**자동 발행은 불가능하다.** 티스토리 Open API는 2024년 2월, 네이버 블로그 글쓰기 API는
2020년 5월에 종료됐다. 붙여넣기 외에 방법이 없다.

```bash
python scripts/blog.py tistory <slug>
```

`dist/tistory/` 아래에 두 가지가 나온다.

| 산출물 | 용도 |
|---|---|
| `<날짜>-<slug>.md` | 프론트매터를 뺀 본문. 에디터에 통째로 붙여넣는다 |
| `<날짜>-<slug>/*.png` | 도식을 PNG로 구운 것. 따로 업로드한다 |

명령 출력에 제목·카테고리·태그·요약이 같이 찍히므로 그대로 옮겨 적으면 된다.

### 왜 PNG인가

도식 원본은 SVG지만 티스토리·네이버 에디터는 SVG 업로드를 받아주지 않는 경우가 많다.
PNG는 어디서나 된다. 폭 1320px(2배 해상도)로 구워 블로그에서 글자가 또렷하다.

변환에는 `svglib`, `reportlab`, `rlPyCairo`가 필요하다.

```bash
python -m pip install svglib reportlab rlPyCairo
```

한글 폰트가 등록되지 않으면 글자가 전부 ■로 나온다. `blog.py`의 `register_korean_fonts()`가
맑은 고딕(Windows)이나 나눔고딕·Noto CJK(Linux)를 찾아 등록하고, 못 찾으면 **에러로 멈춘다.**
깨진 이미지를 조용히 만들어내지 않는다.

### 붙여넣기 절차

1. 티스토리 글쓰기 → 오른쪽 위에서 에디터를 **마크다운**으로 바꾼다
2. `<날짜>-<slug>.md` 내용을 전부 붙여넣는다
3. 본문에 `[[도식 fig/....svg]]` 표식이 남아 있다. 그 자리에 해당 PNG를 업로드해 넣는다
4. 제목·카테고리·태그를 명령 출력대로 입력한다
5. 발행

`dist/`는 git에 올라가지 않는다. 언제든 다시 만들 수 있다.

## 글에 적용되는 규칙

상세 규칙은 [CLAUDE.md](CLAUDE.md)에 있다. 핵심은 다섯이다.

> **1. 검증되지 않은 문장은 쓰지 않는다.** 예제는 실행해 출력까지 확인한 뒤 싣는다.
> 실행할 수 없으면 `manual-only`로 표시하고 **출력을 지어내지 않는다**.
>
> **2. 버전을 반드시 명시한다.** 독자가 "내 버전에서도 그런가"를 판단할 수 있어야 한다.
> 제품 글은 제목에도 버전을 넣는다.
>
> **3. 도식은 공식 자료를 근거로 그리고 출처를 남긴다.** 내부 구조를 추측으로 그리지 않는다.
>
> **4. 회사 내부 정보를 넣지 않는다.** 이 저장소는 공개다. IMS 번호, 고객사,
> 미출시 기능, 사내 경로는 넣지 않는다. 공개 매뉴얼에 있는 내용만 쓴다.
>
> **5. 들어가며는 독자가 겪어봤을 법한 일상 장면으로 시작한다.** 이론 요약으로 시작하지 않는다.

1~3은 `blog.py lint`가 기계적으로 검사한다. 4와 5는 사람이 읽고 판단한다.

# 기술 블로그

IT 기술 글을 매일 2편 작성해 마크다운 원본과 실행 가능한 예제 코드를 함께 보관한다.
주제는 DB·백엔드 60%, IT 전반 40% 비율로 배분한다.

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
└─ scripts/blog.py              운영 CLI
```

## 글 분류

글은 **분야별 폴더**에 들어간다. 경로는 백로그의 `category`와 `subcategory`로 결정된다.

```
posts/
├─ Database/
│  ├─ sqlite/2026-09-18-btree-index-not-used/
│  ├─ oracle/        ← Oracle 전용 글이 생기면 여기에
│  └─ mariadb/
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

## 사용법

```bash
python scripts/blog.py status                 # 백로그 잔량, 발행 비율, 미검증 글
python scripts/blog.py pick                   # 오늘 쓸 주제 2개 선정
python scripts/blog.py new db-001 my-slug     # 글 폴더 스캐폴딩
python scripts/blog.py lint                   # 글 규칙 검사 (길이·도식·출처·링크·검증)
python scripts/blog.py done db-001            # 발행 완료 처리 + 이력 기록
python scripts/blog.py tistory my-slug        # 티스토리용 변환
```

도식을 그린 뒤에는 브라우저로 직접 열어 글자 잘림·겹침을 확인한다.

```bash
python -m http.server 8771 --bind 127.0.0.1
```

Windows 콘솔에서 한글이 깨지면 `PYTHONUTF8=1`을 앞에 붙인다.

## 하루 작업 흐름

1. `pick`으로 주제 2개를 받는다 (core/general 비율을 자동으로 맞춘다)
2. `new`로 폴더를 만든다
3. `code/`에 예제를 작성하고 **실제로 실행해 출력을 확인한다**
4. 공식 문서에서 구조 근거를 찾아 `fig/`에 SVG 도식을 그리고, **도식 아래에 출처를 남긴다**
5. 확인한 출력을 본문에 그대로 싣고 프론트매터 `verified: true`로 바꾼다
6. `lint`를 통과시킨다
7. `done`으로 이력에 기록하고 커밋한다
8. `tistory`로 변환본을 뽑아 에디터에 붙여넣고 발행한다 (도식 SVG는 따로 업로드)

## 글에 적용되는 규칙

상세 규칙은 [CLAUDE.md](CLAUDE.md)에 있다. 핵심은 셋이다.

> **1. 검증되지 않은 문장은 쓰지 않는다.** 예제 코드는 반드시 실행해 출력까지 확인한 뒤 싣는다.
> 실행할 수 없는 예제(상용 DB, 유료 서비스 등)는 본문에 미검증 표시를 남긴다.
>
> **2. 도식은 공식 자료를 근거로 그리고 출처를 남긴다.** 내부 구조를 추측으로 그리지 않는다.
>
> **3. 들어가며는 독자가 겪어봤을 법한 일상 장면으로 시작한다.** 이론 요약으로 시작하지 않는다.

1과 2는 `blog.py lint`가 기계적으로 검사한다. 3은 사람이 읽고 판단한다.

# 운영 가이드

IT 기술 글을 매일 **5편** 작성해 마크다운 원본과 실행 가능한 예제 코드를 함께 보관한다.

| 트랙 | 편수 | 내용 |
|---|---|---|
| **DB 문법** `basics` | 1편 | DB 기본 문법. SQLite로 누구나 재현 가능한 표준 SQL |
| **DB 기능** `product` | 1편 | DB 제품의 기능별 사용법·문법 |
| **기술사** `pe` | 2편 | 정보관리기술사 시험 과목 기술 개념·정의 |
| **일반** `general` | 1편 | 그 외 IT 기술. DB·백엔드 60% + IT 전반 40% |

기본 문법 주제를 다 쓰면 그 자리를 기술사가 가져가 `DB기능 1 + 기술사 3 + 일반 1`이 된다.
어느 쪽이든 하루 5편이다.

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
└─ scripts/blog.py              운영 CLI
```

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

## 사용법

```bash
python scripts/blog.py status                 # 트랙별 잔량, 비율, 미검증·미실행 글
python scripts/blog.py pick                   # 오늘 쓸 주제 선정 (제품 2 + 일반 3)
python scripts/blog.py pick --general 6       # 일반 주제를 더 받아 실행 가능한 것 고르기
python scripts/blog.py new tb-001 my-slug     # 글 폴더 스캐폴딩 (fig/, code/ 포함)
python scripts/blog.py related sequence       # 같은 기능으로 쓴 글 찾기
python scripts/blog.py relink                 # 같은 기능 글끼리 상호 링크 재생성
python scripts/blog.py lint                   # 글 규칙 검사
python scripts/blog.py done tb-001            # 발행 완료 처리 + 이력 기록
python scripts/blog.py tistory my-slug        # 티스토리용 변환
```

도식을 그린 뒤에는 브라우저로 직접 열어 글자 잘림·겹침을 확인한다.

```bash
python -m http.server 8771 --bind 127.0.0.1
```

Windows 콘솔에서 한글이 깨지면 `PYTHONUTF8=1`을 앞에 붙인다.

## 하루 작업 흐름

0. 실행 환경을 확인한다 (`command -v tbsql` 등). 이후 검증 방식이 여기에 달려 있다
1. `pick`으로 제품 2 + 일반 3을 받는다. 같은 기능으로 쓴 글이 있으면 함께 표시된다
2. `new`로 폴더를 만든다
3. 예제를 작성한다
   - 일반 트랙: **실제로 실행해 출력을 확인한다** (`verification: executed`)
   - 제품 트랙에 실행 환경이 없으면: 공식 매뉴얼 근거로 쓰고 `manual-only`로 표시.
     **출력을 지어내지 않는다**
4. 공식 문서에서 구조 근거를 찾아 `fig/`에 SVG 도식을 그리고, **도식 아래에 출처를 남긴다**
5. **버전을 직접 뽑아 `environment`에 숫자까지 적는다**
6. 같은 기능의 글이 있으면 `## 다른 환경에서는` 절로 비교한다
7. `relink`로 상호 링크를 만든다 (기존 글에도 역링크가 생긴다)
8. `verified: true`로 바꾸고 `lint`를 통과시킨다
9. `done`으로 이력에 기록하고 글마다 별도 커밋으로 나눠 커밋·푸시한다
10. `tistory`로 변환본을 뽑아 에디터에 붙여넣고 발행한다 (도식 SVG는 따로 업로드)

`manual-only` 글은 나중에 그 제품이 있는 환경에서 `/blog-daily`를 돌리면 예제를 실제로 돌려
출력을 채우고 `executed`로 승격한다. 새 글보다 이 승격이 우선이다.

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

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
│  └─ YYYY-MM-DD-<slug>/
│     ├─ index.md               본문 (Jekyll/Hugo 호환 프론트매터)
│     └─ code/                  실행 가능한 예제 소스 + README
├─ dist/tistory/                티스토리 붙여넣기용 변환본 (git 추적 제외)
└─ scripts/blog.py              운영 CLI
```

## 사용법

```bash
python scripts/blog.py status                 # 백로그 잔량, 발행 비율, 미검증 글
python scripts/blog.py pick                   # 오늘 쓸 주제 2개 선정
python scripts/blog.py new db-001 my-slug     # 글 폴더 스캐폴딩
python scripts/blog.py done db-001            # 발행 완료 처리 + 이력 기록
python scripts/blog.py tistory my-slug        # 티스토리용 변환
```

Windows 콘솔에서 한글이 깨지면 `PYTHONUTF8=1`을 앞에 붙인다.

## 하루 작업 흐름

1. `pick`으로 주제 2개를 받는다 (core/general 비율을 자동으로 맞춘다)
2. `new`로 폴더를 만든다
3. `code/`에 예제를 작성하고 **실제로 실행해 출력을 확인한다**
4. 확인한 출력을 본문에 그대로 싣고 프론트매터 `verified: true`로 바꾼다
5. `done`으로 이력에 기록하고 커밋한다
6. `tistory`로 변환본을 뽑아 에디터에 붙여넣고 발행한다

## 글에 적용되는 규칙

상세 규칙은 [CLAUDE.md](CLAUDE.md)에 있다. 핵심은 하나다.

> **검증되지 않은 문장은 쓰지 않는다.** 예제 코드는 반드시 실행해 출력까지 확인한 뒤 싣는다.

실행할 수 없는 예제(상용 DB, 유료 서비스 등)는 본문에 미검증 표시를 남긴다.

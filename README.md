# 기술 블로그

IT 기술 글을 하루 9~10편 자동으로 쓰고, 마크다운 원본과 실행 가능한 예제 코드를 함께 보관한다.

- 작성한 글 → **[POSTS.md](POSTS.md)**
- 다른 PC에서 이어받기 → **[SETUP.md](SETUP.md)**
- 운영 전반 (구조·명령어·발행 절차) → **[OPERATIONS.md](OPERATIONS.md)**
- 글쓰기 규칙 → **[CLAUDE.md](CLAUDE.md)**

## 빠르게 보기

```bash
pip install -r requirements.txt
PYTHONUTF8=1 python scripts/blog.py status   # 백로그 잔량
PYTHONUTF8=1 python scripts/blog.py lint     # 글 규칙 검사
```

## 어떻게 굴러가는가

| 시각 | 하는 일 |
|---|---|
| 07:00 · 21:00 | DB 문법 1 + 기술사 개념 1 + (DB 기능 / 리눅스 / 일반 중 1) |
| 15:00 | 정보관리기술사 기출 답안 (단답형 2 또는 논술형 1) |
| 17:00 | 15시 답안에서 나온 개념을 개념 글 2편으로 |
| 09:00 | 전날 회차가 정상이었는지 점검 |

글은 규칙을 통과해야 커밋된다. **검증하지 않은 문장은 쓰지 않고**, 도식에는 근거 문서를
달고, 실행할 수 없는 예제는 "실행 검증 없음"을 밝힌다. 규칙 전문은 [CLAUDE.md](CLAUDE.md)에 있다.

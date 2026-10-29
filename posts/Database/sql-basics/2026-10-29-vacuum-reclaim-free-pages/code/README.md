# VACUUM 예제

DELETE 로 비운 페이지가 어디에 남는지, VACUUM 과 `auto_vacuum` 이 그것을
어떻게 처리하는지 파일 크기·페이지 수·freelist 길이로 확인한다.

의존성은 없다. 파이썬 표준 라이브러리의 `sqlite3` 만 쓴다.

## 실행

```bash
python vacuum_demo.py
```

실행하면 스크립트 옆에 `_work/` 폴더를 만들어 그 안에서 DB 파일 다섯 개를
새로 만든다. 다시 돌리면 폴더째 지우고 시작하므로 결과가 누적되지 않는다.

## 바꿔 볼 값

| 상수 | 기본 | 바꾸면 |
|---|---|---|
| `ROW_COUNT` | `20_000` | 줄이면 페이지 수가 작아져 freelist 차이가 덜 벌어진다 |
| `MEMO_PADDING` | `"x" * 200` | 짧게 하면 한 페이지에 행이 더 들어가 페이지 수가 급감한다 |
| `demo_default()` 의 `id % 10 != 0` | 90% 삭제 | `% 2` 로 바꾸면 50% 삭제가 되고 freelist 가 절반쯤 된다 |
| `PRAGMA incremental_vacuum(100)` | 100 | 숫자가 한 번에 돌려줄 페이지 수다. `1` 로 두면 한 페이지씩 준다 |

`build_database(path, auto_vacuum=...)` 의 인자는 `0`=NONE, `1`=FULL,
`2`=INCREMENTAL 이다. 표를 만들기 **전에** 걸어야 적용된다.

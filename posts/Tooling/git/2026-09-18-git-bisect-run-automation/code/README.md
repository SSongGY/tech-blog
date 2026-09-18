# 예제 코드 — git bisect run 자동화

임시 디렉터리에 커밋 64개짜리 저장소를 만들고, 그중 한 커밋에 퍼센타일 계산 버그를 심은 뒤
`git bisect run`으로 정확히 찾아내는지 확인한다. 실행이 끝나면 임시 저장소는 삭제된다.

## 요구 사항

- Python 3.9 이상 (표준 라이브러리만 사용)
- `git` (PATH에 있어야 한다)

## 실행

```bash
python bisect_demo.py
```

Windows 콘솔에서 한글이 깨지면 `PYTHONUTF8=1`을 앞에 붙인다.

## 시나리오 구성

| 상수 | 값 | 의미 |
|---|---|---|
| `TOTAL_COMMITS` | 64 | 생성할 커밋 수 |
| `BUG_COMMIT_INDEX` | 41 | 이 커밋부터 `percentile` 구현이 잘못된 버전으로 바뀐다 |
| `BROKEN_COMMIT_INDEXES` | (39, 43, 47) | `stats.py`에 문법 오류를 심어 import 자체를 실패시킨다 |

`BROKEN_COMMIT_INDEXES`는 bisect가 **실제로 밟는 지점**에 맞춰 골랐다. 탐색 경로 밖에 두면
skip(125) 경로가 한 번도 실행되지 않아 확인할 수 없다.

## 판정 스크립트의 종료 코드

`git bisect run`이 호출하는 `check_commit.py`는 다음 규약을 따른다.

| 코드 | 의미 | 이 예제에서의 조건 |
|---|---|---|
| 0 | good | `percentile` 결과가 기대값과 일치 |
| 1 | bad | `AssertionError` 또는 `IndexError` |
| 125 | skip | `import stats`가 `SyntaxError`로 실패 |

판정 스크립트는 **저장소 밖**(`workspace/check_commit.py`)에 생성된다. 저장소 안에 두면
과거 커밋을 체크아웃하는 순간 사라진다.

## 바꿔가며 확인할 것

- `BROKEN_COMMIT_INDEXES = ()`로 비우면 테스트 횟수가 이론값 6회로 줄어든다
- `check_commit.py`의 `sys.exit(125)`를 `sys.exit(1)`로 바꾸면 **엉뚱한 커밋**을 범인으로 지목한다
- `TOTAL_COMMITS`를 1024로 올려도 테스트 횟수는 10회 근처에 머문다

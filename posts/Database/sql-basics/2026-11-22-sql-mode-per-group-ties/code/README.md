# 예제 코드 — 그룹별 최빈값과 동점

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.
Python 3.13.5, SQLite 3.49.1 에서 돌렸다. `dbshow.py` 는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python mode_per_group.py
```

## 바꿔 볼 값

- `hongdae` 에 `'latte'` 를 한 건 더 넣으면 동점이 풀린다. [2-1]·[2-2] 와 나머지 방법의 결과가 같아지는지 본다
- [5-1] 의 `RANK()` 를 `DENSE_RANK()` 로 바꿔도 순위 1 만 고르는 한 결과가 같다. 2위를 고를 때 둘이 갈린다
- [7-2] 의 `ORDER BY COUNT(*) DESC, menu` 에서 `menu` 를 빼면 동점 중 어느 것이 나올지 보장되지 않는다
- `group_concat(... ORDER BY ...)` 는 SQLite 3.44.0 부터 된다. 그보다 낮은 판에서는 [7-1] 이 문법 오류를 낸다

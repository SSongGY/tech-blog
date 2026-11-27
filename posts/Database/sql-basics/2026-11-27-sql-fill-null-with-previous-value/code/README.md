# 예제 코드 — NULL을 직전 값으로 채우기

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.
Python 3.13.5, SQLite 3.49.1 에서 돌렸다. `dbshow.py` 는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python fill_forward.py
```

## 바꿔 볼 값

- `reading` 의 S1 09:20 에 값을 넣으면 빈 칸이 이어지는 곳이 사라져 [1] 의 LAG 방식도 전부 채운다
- [4] 의 `ROWS UNBOUNDED PRECEDING` 을 지워도 이 표는 결과가 같다. 키가 `(sensor_id, ts)` 라 같은 ts 가 없기 때문이다 — [6] 이 같은 ts 가 있을 때를 본다
- [4] 의 `MAX` 를 `MIN` 으로 바꿔도 결과가 같다. 묶음 안에 NULL 아닌 값이 하나뿐이기 때문이다
- `build_large` 의 `null_ratio` 를 바꾸면 [8] 에서 방법 A 의 명령 수가 따라 움직인다

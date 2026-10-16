# FIRST_VALUE · LAST_VALUE 프레임 예제

같은 데이터에 윈도우 프레임만 바꿔 가며 일곱 가지를 돌려, `LAST_VALUE` 가
기본 프레임에서 왜 "구간의 끝"이 아닌 값을 돌려주는지 확인한다.
의존성은 없다. 파이썬 표준 라이브러리의 `sqlite3` 모듈만 쓴다.

## 실행

```bash
python window_frame.py
```

## 바꿔 볼 값

- ①의 `ORDER BY salary` 를 지우면 프레임 기본값이 파티션 전체로 바뀐다.
  `LAST_VALUE` 가 ②와 같은 값을 내는지 본다
- ②의 `ROWS` 를 `RANGE` 로 바꿔도 결과가 같은지 본다. 프레임 끝이
  `UNBOUNDED FOLLOWING` 이면 동등 행 처리가 끼어들 자리가 없다
- ⑤의 `2 PRECEDING` 을 `1 PRECEDING` 이나 `3 PRECEDING` 으로 바꿔
  `window_first` 가 어느 행부터 잡히는지 본다
- `SCHEMA` 의 급여 5100 을 하나만 5200 으로 바꾸면 동등 행이 사라진다.
  ④의 `by_range` 와 `by_rows` 가 같아지는지 확인한다

## 파일

| 파일 | 무엇 |
|---|---|
| `window_frame.py` | 예제 본문 |
| `dbshow.py` | 표 정의와 데이터를 출력 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록. 손으로 고치지 않는다 |

# 윈도우 프레임 EXCLUDE 절 예제

메모리 SQLite에 7명짜리 직원 표를 만들고, 윈도우 프레임의 `EXCLUDE` 네 가지
(`NO OTHERS`·`CURRENT ROW`·`GROUP`·`TIES`)가 프레임에서 어떤 행을 빼는지
`group_concat`과 `COUNT(*)`로 찍어 본다. 외부 의존성은 없다.

## 실행

```bash
python window_exclude.py
```

## 바꿔 볼 값

- `build_database()`의 개발 부서 400 두 명 — 동점을 셋으로 늘리면 `EXCLUDE GROUP`과
  `EXCLUDE TIES`가 빼는 사람 수가 같이 늘어난다.
- 3번 질의의 프레임 — `ROWS`를 `GROUPS`로 바꾸면 `EXCLUDE CURRENT ROW`가 동점을
  남기는지 직접 볼 수 있다.
- 9번의 `n` 목록 — 행 수를 두 배로 늘릴 때마다 두 방법의 VDBE 명령 수가 어떻게
  늘어나는지 비교한다.

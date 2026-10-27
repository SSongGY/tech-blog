# 서머타임 경계 예제

`zoneinfo` 로 서머타임 전환 구간의 벽시계 시각을 직접 만들어, 사라지는 시각과
두 번 오는 시각을 뽑아 본다.

## 실행

```bash
python dst_boundary.py
```

## 준비

```bash
python -m pip install -r requirements.txt
```

리눅스·macOS 에는 IANA 타임존 DB 가 시스템에 있으므로 `tzdata` 없이도 돈다.
윈도우에는 없어서 `tzdata` 패키지가 필요하다. 없으면 이렇게 끊긴다.

```text
zoneinfo._common.ZoneInfoNotFoundError: 'No time zone found with key America/New_York'
```

## 파일

| 파일 | 무엇 |
|---|---|
| `dst_boundary.py` | 본 예제. 다섯 절로 나뉘어 있다 |
| `requirements.txt` | `tzdata` 버전 고정 |
| `output.txt` | 실제 실행 기록 |

`tzdata` 버전을 고정해 둔 이유는 타임존 규칙이 **바뀌기 때문**이다. 각국 정부가
서머타임을 폐지하거나 날짜를 옮기면 IANA DB 가 갱신되고, 같은 코드가 다른 값을
내놓는다. 과거 전환 시각도 새 자료가 발견되면 정정된다.

## 바꿔 볼 값

- `NEW_YORK` 을 `ZoneInfo("Europe/Berlin")` 으로 바꾸면 전환 시각이 다르다.
  EU 는 모든 회원국이 UTC 기준 같은 순간에 전환하므로 벽시계 시각이 나라마다 다르다
- `SPRING`·`AUTUMN` 의 연도를 2007 이전으로 바꾸면 미국의 전환일이 달라진다.
  2007년부터 3월 둘째 일요일·11월 첫째 일요일로 옮겨졌다
- 5절의 훑는 범위를 1908~1945 로 바꾸면 더 오래된 전환이 나온다
- `Australia/Lord_Howe` 는 30분만 움직이는 드문 지역이다

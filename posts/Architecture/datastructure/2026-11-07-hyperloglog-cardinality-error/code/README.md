# 예제 코드 — HyperLogLog — 고유 방문자 수를 몇 KB로 세는 원리와 오차

표준 라이브러리만 쓴다. 해시는 `hashlib.blake2b`(4바이트 출력)이고 시행마다 salt 를
바꿔 서로 다른 해시 함수를 흉내 낸다. 난수를 쓰지 않으므로 매번 같은 값이 나온다.

## 실행

```bash
python hyperloglog_demo.py
```

## 바꿔 볼 값

- `section_error_vs_m` 의 `trials` 를 늘리면 실측 RMS 오차가 이론값에 더 가까워지는지 본다
- `estimate()` 에서 작은 범위 보정을 빼고 3절을 다시 돌려 n 이 작을 때 값이 어떻게 되는지 본다
- 4절에서 A·B 의 겹치는 구간을 줄여 교집합 추정의 상대 오차가 어떻게 커지는지 본다

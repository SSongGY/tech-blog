# Text-to-SQL 평가 지표 재현

정답 SQL과 예측 SQL 다섯 쌍을 SQLite에서 비교해 문자열 일치·CM·EM·EX·테스트 스위트·VES가
어떻게 갈리는지 본다. 표준 라이브러리와 같은 폴더의 `dbshow.py`만 쓴다.

## 실행

```bash
python metrics_demo.py
```

## 바꿔 볼 값

- `PAIRS` — 자기 질문과 예측 SQL을 넣어 지표별 판정을 본다.
- `build_database(boundary_row=True)`가 넣는 행 — 다른 경계값을 넣으면 다른 오답이 드러난다.
- `median_time()`의 `runs` — 실행 시간은 환경마다 흔들리므로 R 값은 돌릴 때마다 조금씩 다르다.
  다만 [5]의 R이 1보다 작다는 것(실행계획이 다르다는 것)은 같아야 한다.

`components()`는 Spider 공식 평가 스크립트가 아니다. 최상위 절을 잘라 집합으로 비교하는 원리만 옮겼다.

# 입력값 판정 기능 — 동등 분할·분류 트리 테스트 케이스

명세 하나에서 동등 분할로 4건, 분류 트리로 6건(최소 클래스 커버리지)의
테스트 케이스를 뽑아 구현(`checker.py`)에 돌린다. 같은 케이스가 구현의
분기를 얼마나 덮는지는 coverage.py의 분기 커버리지로 잰다.
명세 기반과 구조 기반이 서로 무엇을 보지 못하는지 확인하려는 것이다.

- `checker.py` — 명세대로 만든 구현. 빈 입력을 따로 거르는 갈래가 하나 더 있다
- `checker_defect.py` — 상한 비교를 `>=`로 쓴 결함 구현
- `run_tests.py` — 케이스 정의, 실행, 커버리지 측정

## 준비

```bash
python -m pip install -r requirements.txt
```

## 실행

```bash
python run_tests.py
```

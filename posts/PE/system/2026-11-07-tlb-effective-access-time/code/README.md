# 예제 코드 — TLB와 유효 메모리 접근 시간

표준 라이브러리만 쓴다. EAT 공식을 계산하고, LRU 로 교체하는 완전 연관 TLB 를
흉내 내 접근 패턴별 적중률을 잰 뒤 공식에 넣어 검산한다.

## 실행

```bash
python tlb_eat.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `tlb_eat.py` | 본문 출력을 내는 스크립트 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `MEMORY_NS`, `TLB_NS` — 시험 문제의 가정값을 넣어 표를 다시 만든다
- `section_patterns()` 의 `entry_count` — TLB 를 65항목으로 늘리면 "65개 페이지 순환"이 어떻게 되는지 본다
- `section_context_switch()` 의 `slice_length` — 교대 간격을 줄이면 비우기 쪽 적중률이 더 떨어진다

시간 값은 측정이 아니라 가정값으로 계산한 것이다. 실제 하드웨어 수치가 아니다.

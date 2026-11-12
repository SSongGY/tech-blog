# 회전 위치 최적화 검산

고정 헤드 드럼에서 SLTF와 MTPT의 총처리시간을, 이동 헤드 디스크에서 SSTF·SPTF·WSTF의
선택과 응답 시간을 계산한다. 표준 라이브러리만 쓴다.

## 실행

```bash
python rotational_scheduling.py
```

## 바꿔 볼 값

- `part1_hand_example()`의 `records` — 레코드 시작·끝 각도를 바꾸면 SLTF와 MTPT 순서가 갈리는지 본다.
- `part2_sstf_vs_sptf()`의 1칸 탐색 시간 목록 — 탐색이 회전보다 느려지면 SPTF도 가까운 쪽을 고른다.
- `simulate()`의 `max_age` — WSTF의 M. 작게 잡을수록 최대 응답은 줄고 처리 효율은 SPTF에서 멀어진다.
- `mtpt_brute()`는 모든 순서를 대입하므로 레코드가 8개를 넘으면 느려진다.

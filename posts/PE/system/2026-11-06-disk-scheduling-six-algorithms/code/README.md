# 디스크 스케줄링 검산

교재(Silberschatz) 예제 큐로 FCFS·SSTF·SCAN·C-SCAN·LOOK·C-LOOK의 헤드 이동 거리를 세고,
슬라이드가 적은 수치(640·236·208)와 맞춰 본다. 표준 라이브러리만 쓴다.

## 실행

```bash
python disk_scheduling.py
```

## 바꿔 볼 값

- `QUEUE`·`HEAD` — 시험 문제의 큐와 시작 위치를 넣으면 여섯 값을 한 번에 검산한다.
- `scan()`·`look()`의 `toward_low` — 처음 움직이는 방향에 따라 거리가 달라진다.
  문제에 방향이 없으면 답안에 가정을 적어야 하는 이유다.
- `part3_sstf_starvation()`의 `±3` — 새 요청이 들어오는 폭을 넓히면 SSTF도 언젠가 먼 요청에 닿는다.

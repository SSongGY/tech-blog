# ATTACH 예제

표준 라이브러리만 쓴다. 두 개의 `.db` 파일을 임시 폴더에 만들고, 한 연결에
붙여 조인·트랜잭션·개수 한계를 차례로 찍는다. 끝나면 임시 폴더째 지워진다.

## 실행

```bash
python attach_demo.py
```

## 바꿔 볼 값

| 어디 | 무엇 | 보이는 것 |
|---|---|---|
| 7절 `range(200)` | 붙이는 횟수 상한 | 이 빌드의 `SQLITE_LIMIT_ATTACHED` 값 |
| 6절 `PRAGMA main.journal_mode` | `WAL` → `DELETE` | 다중 파일 원자성이 보장되는 조합 |
| 3절 ATTACH 순서 | `archive` 를 먼저 열고 `sales` 를 붙이기 | 접두사 없는 `orders` 가 어디로 가는지 |

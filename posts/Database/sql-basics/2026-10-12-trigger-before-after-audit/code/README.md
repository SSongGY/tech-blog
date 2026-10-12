# 예제 코드 — 트리거 기본

계좌 표에 `AFTER INSERT`·`AFTER UPDATE`·`AFTER DELETE` 트리거를 걸어 변경 이력 표를 채우고,
`BEFORE UPDATE` 트리거와 `RAISE()`로 잘못된 변경을 막는다. 트리거가 실패하면 원래 문장이
어떻게 되는지, `RAISE(IGNORE)`가 무엇을 버리는지, `UPDATE OF`에 없는 컬럼 이름을 쓰면 어떻게
되는지, `rowcount`와 `total_changes`가 트리거의 변경을 어떻게 세는지 확인하고, 10만 행
`UPDATE`에서 이력 트리거가 더하는 시간을 잰다. 파이썬 표준 라이브러리만 쓴다.
`dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python trigger_basics.py
```

## 바꿔볼 값

- 1번 `tr_account_update`의 `WHEN OLD.balance IS NOT NEW.balance`를 지우고 1-D의 이력이 생기는지 본다.
- 2번 `RAISE(ABORT, ...)`를 `RAISE(FAIL, ...)`로 바꾸고 2-B에서 1·2번 계좌가 바뀐 채로 남는지 본다.
- `BULK_ROWS`를 100만으로 올려 8번의 배율이 유지되는지 본다.

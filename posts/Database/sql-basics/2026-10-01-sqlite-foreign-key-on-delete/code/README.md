# 예제 코드 — 외래 키 — 참조 무결성과 ON DELETE

`foreign_key_basics.py` 하나로 외래 키 검사가 꺼져 있을 때와 켜져 있을 때의 차이,
`ON DELETE` 동작 다섯 가지, 부모 키 조건, 자식 키 인덱스의 효과를 차례로 확인한다.
표준 라이브러리만 쓰고 메모리 DB에서 돈다.

## 실행

```bash
python foreign_key_basics.py
```

## 바꿔 볼 값

- 8번의 `DEFERRABLE INITIALLY DEFERRED` 를 지운다. `NO ACTION` 도 `DELETE` 에서 바로 막히는지 본다.
- 9번의 `email TEXT` 를 `email TEXT UNIQUE` 로 바꾼다. 에러가 사라지는지 본다.
- 10번의 `20000` 을 `2000` 으로 줄인다. 인덱스가 없을 때의 명령 수가 행 수에 비례해 줄어드는지 본다.

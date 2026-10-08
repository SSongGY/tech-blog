# 예제 코드 — 생성 컬럼 VIRTUAL과 STORED

주문 항목 표에 `단가 × 수량`과 `주문 월`을 생성 컬럼으로 두고, VIRTUAL과 STORED가 어디서
갈리는지 SQLite로 확인한다. 값이 따라 바뀌는 것, 직접 넣으려 할 때의 에러, `ALTER TABLE`로
추가할 수 있는 쪽, `PRAGMA table_info`와 `table_xinfo`의 차이, 쓸 수 없는 식(기본값·PK·
비결정 함수·서브쿼리), 생성 컬럼 위의 인덱스와 실행계획, 그리고 10만 행에서 저장 공간과
조회 시간을 잰다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다. `dbshow.py`는 표 정의와
데이터를 찍는 도우미다. 측정 부분은 임시 폴더에 파일 DB를 만들고 끝나면 지운다.

## 실행

```bash
python generated_columns.py
```

## 바꿔볼 값

- `BULK_ROWS`를 100만으로 올리면 파일 크기 차이와 조회 시간 차이가 비례해 커지는지 본다.
- 10번의 질의에서 `line_total`(VIRTUAL) 대신 식 `unit_price * quantity`를 직접 쓰면 식 인덱스를 타는지 본다.
- `order_month`를 VIRTUAL로 바꾸면 인덱스가 식 인덱스로 바뀌는지 `sqlite_master`의 정의로 본다.

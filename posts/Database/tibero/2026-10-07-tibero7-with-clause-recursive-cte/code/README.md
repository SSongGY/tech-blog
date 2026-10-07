# 예제 코드 — Tibero 7 WITH 절

**아직 실행하지 않았다.** 글을 쓴 시점에 검증용 인스턴스에 접속할 수 없었다(`TBR-2131`).
인스턴스가 살아나면 이 스크립트를 돌려 출력을 채우고 글을 `executed`로 올린다.

빈 스키마에 조직 표(`dept_unit`)와 매출 표(`unit_sales`)만 만든다. 보통 CTE, 이어 쓰는 CTE,
재귀 CTE, `SEARCH DEPTH FIRST`·`BREADTH FIRST`, `CYCLE` 절, 같은 트리의 `CONNECT BY`, 재귀 WITH를
`INSERT`의 원본으로 쓰기를 차례로 돌린다. 순환 데이터는 `UPDATE` 뒤 `ROLLBACK`으로 되돌리고,
마지막에 표를 지운 뒤 `user_objects`가 0개인지 찍는다. 다른 객체는 조회하지 않는다.

## 실행

```bash
tbsql -s <사용자>/<암호> @with_clause.sql
```

tbsql 스크립트 모드에서는 문장 뒤 같은 줄에 `--` 주석을 달면 다음 문장이 깨지므로 설명은 `PROMPT`로 적었다.
파일 끝의 `EXIT`가 없으면 프롬프트에서 대기한다.

## 확인할 것

매뉴얼에 적혀 있지 않거나 예제로만 확인되는 항목이다. 돌린 뒤 글에 반영한다.

- 3번 — 재귀 CTE에서 `col_alias` 목록을 빼면 어떤 에러가 나는지. 매뉴얼 예제는 전부 목록을 적는다.
- 3번 — `UNION ALL` 대신 `UNION`을 쓰면 되는지, 에러인지.
- 4번·5번 — `SEARCH ... SET seq`의 `seq`가 1부터 연속인지, `ORDER BY seq` 없이도 그 순서로 나오는지.
- 7번 — 재귀 멤버 자체에 `SUM`을 넣으면 에러인지(이 스크립트는 바깥 `GROUP BY`로 우회했다).
- 8-A — `CYCLE` 절 없이 순환을 만나면 어떤 에러 번호가 나는지. 매뉴얼은 "에러를 출력한다"고만 적는다.
- 8-B — `CYCLE unit_id`가 검출한 행이 깊이 몇에서 나오는지, 그 행이 결과에 포함되는지.
- 8-C — `NOCYCLE` 없는 `CONNECT BY`의 에러 번호(계층 질의 글에서는 `TBR-10064`였다).
- 9번 — `INSERT INTO ... WITH ... SELECT` 형태가 그대로 되는지, `WITH`를 `INSERT` 앞에 둬야 하는지.

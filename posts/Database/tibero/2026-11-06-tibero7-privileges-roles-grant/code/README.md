# 예제 코드 — Tibero 7 권한과 롤

**아직 실행하지 않았다.** 이 글을 쓸 때 Tibero 인스턴스에 접속할 수 없어(`TBR-2131`)
매뉴얼 근거로만 썼다. 아래 스크립트는 실행 환경이 생기면 그대로 돌려 출력을 채우고
글을 `executed` 로 올리기 위한 것이다.

## 실행

```bash
tbsql -s tibero/tmax @privileges_roles.sql
```

`CREATE USER`·`CREATE ROLE`·`DROP USER` 를 하므로 DBA 권한 계정으로 돌린다.
접속 계정은 환경에 맞게 바꾼다.

## 파일

| 파일 | 무엇 |
|---|---|
| `privileges_roles.sql` | 1) ADMIN OPTION 회수 2) GRANT OPTION 연쇄 회수 3) 롤에 GRANT OPTION 4) 기본 롤·SET ROLE 5) REFERENCES 와 CASCADE CONSTRAINTS |

## 확인할 것

- 1절: `PV_END` 의 `CREATE VIEW` 가 남는가 (매뉴얼: 남는다)
- 2절: 회수 뒤 `PV_END` 의 `SELECT` 가 사라지는가 (매뉴얼: 사라진다)
- 3절: 첫 문장이 에러인가 (매뉴얼: 롤에는 WITH GRANT OPTION 불가). 에러 번호는 매뉴얼에 없다
- 5절: 첫 `REVOKE` 가 `TBR-17005` 인가

스크립트는 예제 사용자 `PV_*` 와 롤 `PV_READER` 만 만들고 마지막에 전부 지운다.
tbsql 스크립트 모드에서는 문장 뒤 같은 줄에 주석을 달지 않는다(다음 문장이 깨진다).

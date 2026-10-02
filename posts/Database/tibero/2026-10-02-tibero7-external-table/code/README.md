# 예제 코드 — Tibero 7 외부 테이블

**아직 실행하지 않았다.** 글을 쓴 시점에 검증용 Tibero 인스턴스에 접속할 수 없었다(`TBR-2131`).
접속되는 환경에서 아래 순서로 돌려 출력을 채우고 글을 `verification: executed`로 올린다.

- `members.csv` — 머리글 1줄 + 데이터 4줄. 3번 줄은 쉼표를 `\`로 이스케이프했고, 4번 줄은 마지막 필드가 없다
- `external_table.sql` — 디렉터리 객체 생성, 매뉴얼 예제 모양의 외부 테이블, 머리글 건너뛰기 유무,
  DML·인덱스·제약 시도, 없는 파일·없는 경로, 사전 뷰 조회, 정리까지 한 번에 돈다

## 실행

`members.csv`는 DB 서버 쪽 `/tmp/blog_ext/`에 둔다. 디렉터리 경로를 클라이언트가 아니라 서버가
해석한다는 것은 매뉴얼 문장에 직접 적혀 있지 않으므로, 이것도 실행으로 확인할 항목이다.
스크립트는 `CREATE ANY DIRECTORY` 특권이 있는 계정으로 돌린다.

```bash
ssh <db-host> 'mkdir -p /tmp/blog_ext'
scp members.csv external_table.sql <db-host>:/tmp/blog_ext/
ssh <db-host> 'bash -lc "tbsql -s <user>/<password> @/tmp/blog_ext/external_table.sql"'
ssh <db-host> 'rm -rf /tmp/blog_ext'
```

## 바꿔볼 값

- 3번 단계를 돌린 뒤 서버의 `members.csv`에 줄을 하나 더하고 같은 `SELECT`를 다시 돌린다. 테이블을 다시 만들지 않아도 행이 느는지 본다.
- `members.csv`를 CRLF 줄 끝으로 저장해 올리면 `LINES TERMINATED BY '\n'`에서 마지막 컬럼 값 끝에 CR이 붙는지 본다.
- 4번 줄의 빠진 필드가 NULL로 읽히는지, 오류 행으로 빠지는지 본다. tbLoader의 `TRAILING NULLCOLS`를 `ACCESS PARAMETERS`에 넣으면 달라지는지도 본다.

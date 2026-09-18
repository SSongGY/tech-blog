# 예제 코드 — Tibero 7 시퀀스

`sequence_examples.sql` 하나다. **이 스크립트는 실행 검증을 거치지 않았다.**
작성 환경에 Tibero 클라이언트(`tbsql`)가 없어 문법만 매뉴얼 근거로 정리했다.

## 실행

```bash
tbsql <사용자>/<비밀번호> @sequence_examples.sql
```

시퀀스를 만들려면 `CREATE SEQUENCE` 시스템 특권이 필요하고, 다른 사용자의 스키마에
만들려면 `CREATE ANY SEQUENCE`가 필요하다.

## 바꿔볼 값

| 위치 | 기본값 | 바꾸면 |
|---|---|---|
| `CACHE 100` | 100 | `NOCACHE`로 바꾸면 값을 요청할 때마다 데이터 사전을 갱신한다 |
| `INCREMENT BY` | 1 | 음수로 두면 감소한다. 이때 `START WITH` 기본값은 `MAXVALUE`가 된다 |
| `CYCLE` / `NOCYCLE` | `NOCYCLE` | `slot_seq`의 12를 넘겨 호출해 보면 차이가 드러난다 |
| `ORDER` / `NOORDER` | `NOORDER` | 클러스터 환경에서만 지정할 수 있다 |

## 확인해 볼 것

- 8번 `ALTER SEQUENCE` 전후로 `NEXTVAL`을 뽑아 번호가 얼마나 건너뛰는지 센다.
  캐시 개수만큼 누락될 수 있다.
- `user_sequences`의 캐시 관련 컬럼을 조회해 **이 인스턴스의 기본 캐시 개수**를 확인한다.
  매뉴얼은 `CACHE`를 생략했을 때의 기본 개수를 명시하지 않는다.
- **컬럼 `DEFAULT`에 `NEXTVAL`을 쓸 수 있는지 직접 확인한다.** 매뉴얼 두 페이지가
  반대로 적고 있다. 스키마 객체 페이지는 사용 불가 목록에 넣고, `CREATE TABLE` 페이지의
  `DEFAULT expr` 항목은 지정할 수 있다고 한다. 실행이 유일한 판정 수단이다.
- `slot_seq`의 `CACHE 4`를 `CACHE 20`으로 바꿔 생성해 본다. 사이클이 12개이므로
  에러 7340(`ERROR_DDL_SEQ_CACHE_OVER_ONE_CYCLE`)이 나야 한다.
- `countdown_seq`를 소진시켜 에러 6004(`ERROR_DD_SEQ_OVERFLOW`)를 확인한다.
  `NOCYCLE` 시퀀스가 한계에 닿았을 때의 동작이다.
- `CURRVAL`을 `NEXTVAL`보다 먼저 호출해 에러 6003을 확인한다.

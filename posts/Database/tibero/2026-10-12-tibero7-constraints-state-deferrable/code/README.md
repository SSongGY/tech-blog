# 예제 코드 — Tibero 7 제약조건의 상태와 지연 검사

**아직 실행하지 않았다.** 글을 쓴 시점에 검증용 인스턴스에 접속할 수 없었다(`TBR-2131`).
인스턴스가 살아나면 이 스크립트를 돌려 출력을 채우고 글을 `executed`로 올린다.

빈 스키마에 부서(`cs_dept`)·사원(`cs_emp`) 표를 만들고 PRIMARY KEY·UNIQUE·NOT NULL·CHECK·FOREIGN KEY를 하나씩 건다.
CHECK를 끄고 위반 행을 넣은 뒤 `ENABLE VALIDATE`와 `ENABLE NOVALIDATE`가 어떻게 갈리는지, UNIQUE에
`NOVALIDATE`를 주면 무엇이 되는지, `DISABLE VALIDATE`에서 DML이 막히는지를 차례로 본다. 좌석 표 두 개
(`cs_seat` 지연 검사, `cs_seat_now` 즉시 검사)로 값 맞바꾸기를 해 보고, FOREIGN KEY에 `DEFERRABLE`을 줘 본다.
마지막에 표를 전부 지우고 `user_objects`가 0개인지 찍는다. 다른 객체는 조회하지 않는다.

## 실행

```bash
tbsql -s <사용자>/<암호> @constraint_states.sql
```

tbsql 스크립트 모드에서는 문장 뒤 같은 줄에 `--` 주석을 달면 다음 문장이 깨지므로 설명은 `PROMPT`로 적었다.
파일 끝의 `EXIT`가 없으면 프롬프트에서 대기한다.

## 확인할 것

매뉴얼에 적혀 있지 않거나 두 문서의 문장이 갈리는 항목이다. 돌린 뒤 글에 반영한다.

- 1-B — FOREIGN KEY 컬럼(`cs_emp.dept_no`)에 인덱스가 생기는지. 공통 문법 요소 페이지 안에서 "FK는 비유일 인덱스에
  같은 동작"과 "FK 컬럼에 인덱스를 생성하지 않는다"가 함께 적혀 있다.
- 1-A — 이름을 주지 않은 NOT NULL 제약의 `GENERATED` 값과 이름 형태.
- 3-A — 기존 위반 행이 있을 때 `ENABLE VALIDATE`의 에러 코드와 문구.
- 4 — UNIQUE를 `ENABLE NOVALIDATE`로 켤 때 중복 행이 있으면 실패하는지. 관리자 안내서는 기본 키·유일 키는
  NOVALIDATE를 줘도 VALIDATE로 동작한다고 적는다. 성공한다면 `VALIDATED` 칸에 무엇이 찍히는지.
- 5 — `DISABLE VALIDATE` 상태에서 INSERT·UPDATE가 어떤 에러로 막히는지.
- 5-A — UNIQUE를 `DISABLE VALIDATE`로 바꿨을 때 인덱스가 남는지. 관리자 안내서 문장("인덱스를 드롭하고 해당 제약조건
  컬럼을 변경할 수 없음")은 두 가지로 읽힌다.
- 6 — 참조되는 PK를 CASCADE 없이 DISABLE 할 때의 에러.
- 7 — 지연 검사 UNIQUE가 어떤 인덱스(유일/비유일)를 쓰는지, 7-A의 에러 코드, 7-C에서 `park` 행까지 사라지는지.
- 8 — FOREIGN KEY에 `DEFERRABLE`을 줬을 때의 에러. 문법 도식이 이미지라 `DEFERRABLE`의 자리(제약 뒤)는 확인하지 못했다.

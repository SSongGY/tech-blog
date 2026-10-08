# 예제 코드 — 인증서 검증 경로와 폐기 확인

`openssl`로 루트 CA → 중간 CA → 서버 인증서 3단 체인을 만들고, 검증 경로가 끊기는 경우(중간 CA 누락),
CRL로 폐기를 확인하는 경우(CRL 없음·폐기됨·만료됨·중간 CA 폐기), OCSP로 확인하는 경우(good·revoked·unknown·서명자 용도 위반)를
차례로 돌린다. 키와 인증서는 실행할 때마다 `probe_pki/`에 새로 만든다(저장소에 올라가지 않는다).
`ca.cnf`는 두 CA가 함께 쓰는 설정이고, 어느 CA인지는 환경변수 `CA_DIR`로 고른다.

Git Bash의 OpenSSL 3.5.6에서 돌렸다. 리눅스에서는 `MSYS_NO_PATHCONV=1`이 아무 일도 하지 않으므로 그대로 돌아간다.

## 실행

```bash
bash pki_lab.sh
```

## 바꿔볼 값

- `ca.cnf`의 `default_crl_days`를 7로 바꾸면 2-6번(이틀 뒤 검증)이 통과한다.
- 3-2번에서 `-CRLfile "$work/root.crl"`을 빼면 루트 CA의 CRL을 못 구해 다른 오류로 실패한다.
- 4-1번의 `-no_nonce`를 빼고 요청 쪽에서도 nonce를 넣으면, `-index` 방식 응답기는 nonce를 돌려주므로 재전송 방지 확인이 된다.

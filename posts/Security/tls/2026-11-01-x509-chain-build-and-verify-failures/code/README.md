# 인증서 체인을 직접 만들어 검증 실패 문구를 모으는 예제

루트 CA → 중간 CA → 서버 인증서를 만들고, 체인을 한 군데씩 망가뜨려
`openssl verify` 가 내는 문구를 모은다. openssl 하나만 있으면 돌아간다.

## 실행

```bash
bash build_chain.sh
```

생성물은 전부 `probe_work/` 아래에 들어가고 실행할 때마다 지워졌다 다시 만들어진다.
`ext/` 의 네 파일은 인증서에 넣을 확장(extension) 정의다.

## 바꿔볼 값

- `ext/intermediate.ext` 의 `pathlen:0` 을 `pathlen:1` 로 바꾸면 8번 시나리오가 통과한다.
  루트가 중간 CA 에게 "너 아래로 한 단계까지"라고 적어 주는 자리다.
- `ext/server.ext` 의 `subjectAltName` 에 `DNS:example.com` 을 추가하면 6번의 마지막
  검증이 통과한다. 와일드카드로 `DNS:*.example.com` 을 넣어 보면 `shop.example.com` 은
  맞지만 `a.b.example.com` 은 안 맞는 것도 확인된다.
- 5번의 `-attime 1709251200` 은 2024-03-01 00:00:00 UTC 다. 숫자를 만료일 뒤로 옮기면
  다시 실패한다. 인증서가 아니라 시계가 판정을 바꾸는 자리다.
- `ext/server.ext` 의 `extendedKeyUsage` 를 `clientAuth` 로 바꾸고 `verify` 에
  `-purpose sslserver` 를 붙이면 용도 불일치가 잡힌다.

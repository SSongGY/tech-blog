# ssh_config 해석 확인 예제

`ssh -G` 로 설정 파일이 실제로 어떤 값으로 풀리는지 확인한다.
**접속은 한 번도 하지 않는다.** `-G` 는 설정을 해석해 최종값만 찍고 끝내는 옵션이라
SSH 서버 없이도 돌아간다.

예제에 쓰는 IP는 전부 문서용으로 예약된 대역(RFC 5737의 `203.0.113.0/24`, `198.51.100.0/24`)이고,
도메인은 `example.com` 이다. 실재하는 호스트를 가리키지 않는다.

## 실행

```bash
bash ssh_config_demo.sh
```

설정 파일은 실행할 때마다 `probe_work/` 아래에 새로 만들어진다
(`probe*` 는 gitignore 대상이라 저장소에 남지 않는다).

## 바꿔 볼 값

- `order-top.conf` 의 `Host *` 블록을 아래로 내려 보고 `user` 가 어떻게 달라지는지 본다
- `match.conf` 의 `Match originalhost short` 를 `Match host 203.0.113.40` 으로 바꾸면
  `short` 가 더는 안 걸린다. `originalhost` 와 `host` 가 무엇을 비교하는지 드러난다
- `include-rel.conf` 의 `Include` 줄을 `~/.ssh/...` 로 바꾸면 그쪽은 걸린다

## 파일

| 파일 | 무엇 |
|---|---|
| `ssh_config_demo.sh` | 예제 본문 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록. 손으로 고치지 않는다 |
| `probe_*` | 찔러 본 스크립트와 실행 중 생기는 설정 파일. 저장소에 올라가지 않는다 |

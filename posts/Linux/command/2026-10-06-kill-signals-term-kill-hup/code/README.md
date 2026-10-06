# 예제 코드 — kill과 시그널

`kill_signals.sh`가 `bash -c`로 작은 작업을 띄우고 bash 내장 `kill`로 시그널을 보낸 뒤,
받는 쪽이 어떻게 반응했는지(핸들러 출력, `wait` 종료 코드, `kill -0` 생존 여부)를 찍는다.
`timeout`은 GNU coreutils 판이다. 작업 파일은 `probe_work/`에 생기고 gitignore 된다.
외부 의존성은 없다. 한 번 도는 데 20초쯤 걸린다.

필요한 것: bash 5.x(`EPOCHREALTIME`·`trap -P`), GNU coreutils `timeout`.

## 실행

```bash
bash kill_signals.sh
```

## 바꿔볼 값

- 1번의 이름 목록은 플랫폼마다 번호가 다르다. 리눅스 x86에서 돌리면 `USR1`·`STOP`·`CONT`·`CHLD` 번호를 이 기록과 비교한다.
- 8번의 `sleep 3`을 `sleep 10`으로 늘리면 포그라운드 쪽의 지연이 따라 늘어나는지 본다.
- 9번에서 `set -m`을 지우고 `-PGID`로 보낸 시그널이 어디까지 닿는지 본다.
- 12번의 `-k 1`을 `-k 0.2`로 줄여 KILL까지 걸리는 시간을 본다.

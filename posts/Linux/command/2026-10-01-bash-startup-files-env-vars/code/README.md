# 예제 코드 — 환경변수와 셸 초기화 순서

가짜 HOME(`/tmp/shinit/home`)에 `~/.bash_profile`·`~/.bash_login`·`~/.profile`·`~/.bashrc`·`~/.bash_logout` 등을 깔고,
각 파일이 읽히면 `[읽음] ~/파일` 한 줄을 찍게 한 뒤 bash를 여러 방식으로 띄운다. 새 셸은 `env -i`로 빈 환경에서 띄운다.
끝나면 `/tmp/shinit`을 지운다. 사용자의 실제 HOME은 건드리지 않는다.

| 장 | 무엇을 보는가 |
|---|---|
| 0 | bash·env 버전 |
| 1 | `-c`, `-l`, `-i`, `-l -i`, 스크립트, `BASH_ENV` — 방식마다 읽는 파일, `exit`와 `~/.bash_logout` |
| 2 | 로그인 셸의 `.bash_profile` → `.bash_login` → `.profile` 우선순위, `.bash_profile`에서 `.bashrc` 읽기 |
| 3 | `--noprofile`, `--norc`, `--rcfile`, `--init-file` |
| 4 | `sh`로 띄울 때와 `--posix` — `ENV` 변수 |
| 5 | 셸 변수와 환경변수 — `export`, `export -n`, `export -p`, `export -f`, `declare -p`, 한 명령에만 주기, `set -a`, `source` |
| 6 | `env` 옵션 `-i`·`-`·`-u`·`-C`·`-0`·`-S`·`-v`·`--ignore-signal`·`--list-signal-handling`, `printenv` |
| 7 | `.bashrc`에서 PATH를 늘릴 때 겹으로 쌓이는 것, 빈 환경의 기본 PATH |

`/etc/profile`·`/etc/bash.bashrc`는 고칠 수 없으므로 그 파일이 남기는 변수(`CONFIG_SITE`, `CYG_SYS_BASHRC`)로 읽혔는지를 판별한다.
두 변수는 Git Bash(Git for Windows)의 시스템 파일이 세우는 것이다. 리눅스 배포판에서는 이 판별 줄을 배포판의 시스템 파일에 맞게 바꿔야 한다.

## 실행

```bash
bash bash_startup_env.sh
```

## 바꿔볼 값

- 2장에서 `.bashrc`만 남기고 `.bash_profile`·`.bash_login`·`.profile`을 모두 지운 뒤 `bash -l`을 띄워 본다. Git Bash의 `/etc/profile.d/bash_profile.sh`가
  경고를 찍고 `~/.bash_profile`을 새로 만든다(이 예제는 그 동작을 피하려고 셋 중 하나를 늘 남긴다).
- 7-A의 세 겹을 다섯 겹으로 늘려 `/opt/demo/bin`이 몇 번 붙는지 본다.

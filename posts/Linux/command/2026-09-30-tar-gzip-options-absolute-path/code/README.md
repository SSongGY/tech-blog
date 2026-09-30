# 예제 코드 — tar와 gzip: 압축과 해제, 그리고 옵션 순서

GNU tar 1.35와 gzip 1.14의 자주 쓰는 옵션을 갈래별로 돌린다. 모든 파일은 `/tmp/tardemo` 아래에 만들고
끝나면 지운다. 4·5장은 `-P`로 **작업 폴더 밖의 경로에 쓰는** 동작을 보이지만, 그 경로도 `/tmp/tardemo` 안이다.

| 장 | 무엇을 보는가 |
|---|---|
| 0 | 버전, 깔린 압축 프로그램, `--show-defaults` |
| 1 | 동작 모드 `-c -t -x -r -u -A --delete`, 둘을 함께 주면 거절 |
| 2 | 옵션 쓰는 법 세 가지와 `-cfv`가 `v`라는 아카이브를 만드는 것 |
| 3 | `-z -j -J --zstd -a -I`, 읽을 때의 압축 자동 판별 |
| 4 | 절대경로 — 만들 때 `/`를 떼는 것과 `-P` |
| 5 | `../`가 든 이름을 풀 때 거절하는 것과 `-P` |
| 6 | 풀기 전에 목록에서 절대경로·`..`을 찾는 법 |
| 7 | `-C`, `--strip-components`, `--transform`, `--one-top-level`, 일부만 풀기, `--wildcards`, `-O`, `--to-command` |
| 8 | 덮어쓰기 `-k`, `--skip-old-files`, `--keep-newer-files`, `--backup` |
| 9 | `--exclude`, `--exclude-vcs`, `-T`, `--null`, `--no-recursion`, `-N`와 `--newer-mtime`, `--remove-files` |
| 10 | 재현 가능한 아카이브 — `--sort --mtime --owner --group --numeric-owner` |
| 11 | `-d` 비교, `-W` 검증, `-g` 증분 |
| 12 | `--totals`, `--checkpoint`, `-R`, `--full-time`, `--index-file`, 종료 코드 |
| 13 | gzip 단독 — `-d -k -f -c -l -t -1..-9 -S -v -n -N -r -q` |

## 실행

```bash
bash tar_gzip_options.sh
```

Git Bash(Windows)에서 돌렸다. 리눅스에서도 그대로 돈다. 목록의 소유자 칸에 계정 이름이 찍히지 않도록
`-tv` 에는 `--numeric-owner`를 붙였다.

## 바꿔볼 값

- 3장에 `zstd`가 깔린 환경이면 `--zstd` 줄이 성공하고 크기 비교에 넣을 수 있다.
- 7장 `--transform`의 식을 `s,^app,myapp,`으로 바꾸면 `apple/` 같은 이름까지 바뀌는지 본다.
- 13장 `seq 1 50000` 대신 로그 파일을 넣고 `-1`과 `-9`의 크기를 다시 비교한다.

#!/usr/bin/env bash
# xargs 옵션을 갈래별로 하나씩 돌린다.
# 임시 폴더에 공백·따옴표·줄바꿈이 든 파일 이름을 만들고, 끝나면 지운다.

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT
cd "${WORK_DIR}" || exit 1

# 명령 문자열을 그대로 찍고 돌린다. stderr 를 합쳐야 출력 순서가 보존된다
show() {
  echo "\$ $1"
  eval "$1" 2>&1
  echo "[종료 코드 $?]"
  echo
}

section() {
  echo "================================================================"
  echo "$1"
  echo "================================================================"
}

make_files() {
  mkdir logs
  touch "logs/app.log" "logs/report 2026.log" "logs/it's.log"
  touch "logs/$(printf 'two\nlines.log')"
  printf 'alpha\nbeta\ngamma\n' > items.txt
}

section "0. 환경"
xargs --version | head -n 1
bash --version | head -n 1
xargs --show-limits < /dev/null 2>&1
echo
make_files

section "1. 입력을 어떻게 나누는가 — 기본은 공백과 줄바꿈"
show "printf 'a b\nc\n' | xargs -n 1 echo"
show "echo \"'a b' c\" | xargs -n 1 echo"
show "echo 'a\\ b c' | xargs -n 1 echo"
show "printf 'hi\n' | xargs"

section "2. 공백 든 파일 이름 — 기본 모드가 깨지는 자리"
show "find logs -name '*.log' | sort | xargs ls -1"
show "find logs -name '*.log' | sort | xargs -d '\n' ls -1"
show "find logs -name '*.log' -print0 | sort -z | xargs -0 ls -1"
show "find logs -name '*.log' -print0 | sort -z | xargs -0 -n 1 printf '[%s]\n'"

section "3. 입력 끝 — -E, -a"
show "printf 'a\nSTOP\nb\n' | xargs -E STOP echo"
show "printf 'a\0STOP\0b\0' | xargs -0 -E STOP echo"
show "xargs -a items.txt echo"

section "4. 한 번에 몇 개씩 — -n, -L, -l"
show "printf '1 2 3\n4 5\n6\n' | xargs -n 2 echo"
show "printf '1 2 3\n4 5\n6\n' | xargs -L 1 echo"
show "printf '1 2 \n3\n4\n' | xargs -L 1 echo"
show "printf '1 2\n\n3\n' | xargs -l echo"

section "5. 명령줄 길이 — -s, -x"
show "seq 1 12 | xargs -s 20 echo"
show "seq 1 12 | xargs -s 20 -x echo"
show "seq 1 12 | xargs -n 10 -s 20 echo"
show "seq 1 12 | xargs -n 10 -s 20 -x echo"
show "echo 123456789012345678901234567890 | xargs -s 20 echo"

section "6. 자리 바꿔 넣기 — -I, -i"
show "printf 'a b\nc\n' | xargs -I {} echo '<{}>'"
show "printf 'x\ny\n' | xargs -I @ echo @-@"
show "printf 'x\ny\n' | xargs -i echo 'item={}'"
show "printf '  lead\n' | xargs -I {} echo '<{}>'"

section "7. 빈 입력 — -r"
show "printf '' | xargs echo 'ran with:'"
show "printf '' | xargs -r echo 'ran with:'"

section "8. 실행 전에 보여 주기 — -t"
show "printf 'a\nb\nc\n' | xargs -t -n 2 echo"

section "9. 병렬 — -P, --process-slot-var"
show "printf '0.6\n0.2\n0.4\n' | xargs -n 1 sh -c 'sleep \"\$0\"; echo done \$0'"
show "printf '0.6\n0.2\n0.4\n' | xargs -P 3 -n 1 sh -c 'sleep \"\$0\"; echo done \$0'"
elapsed() {
  local started ended
  started=$(date +%s%N)
  seq 1 4 | xargs -P "$1" -n 1 sh -c 'sleep 0.5' >/dev/null
  ended=$(date +%s%N)
  echo "-P $1 : $(( (ended - started) / 1000000 )) ms"
}
echo "\$ seq 1 4 | xargs -P N -n 1 sh -c 'sleep 0.5'   (N = 1, 2, 4)"
elapsed 1
elapsed 2
elapsed 4
echo
show "seq 1 4 | xargs -P 2 -n 1 --process-slot-var=SLOT sh -c 'echo item \$0 slot \$SLOT' | sort"
show "seq 1 6 | xargs -P 0 -n 3 echo | sort"

section "10. 종료 코드"
show "printf 'a\n' | xargs sh -c 'exit 1'"
show "printf 'a\nb\n' | xargs -n 1 sh -c 'echo run \$0; exit 255'"
show "printf 'a\n' | xargs no-such-command"
printf 'echo hi\n' > not_exec.sh
show "printf 'a\n' | xargs ./not_exec.sh"
show "printf 'a\n' | xargs -s 1 echo"

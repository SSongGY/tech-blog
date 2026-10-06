#!/usr/bin/env bash
# kill 과 시그널을 갈래별로 실제로 보내 보고, 받는 쪽이 어떻게 반응하는지 찍는다.
# 받는 쪽은 bash -c 로 띄운 작은 작업이다. trap 을 걸어 두면 시그널을 받은 순간이 출력에 남는다.

# 작업 파일은 code/probe_work 에 둔다 (gitignore 대상). 경로를 출력에 찍지 않는다
mkdir -p probe_work && cd probe_work || exit 1
rm -f app.lock app.conf child.pid tick.log

# 자식이 실행을 마치고 trap 을 걸 시간을 준다.
# 그 전에 보내면 아직 trap 이 없어 기본 동작이 일어난다
settle() { sleep 0.5; }

alive() {
    if kill -0 "$1" 2>/dev/null; then echo "살아 있음 (kill -0 → 0)"; else echo "없음 (kill -0 → 1)"; fi
}

now_ms() { local t=${EPOCHREALTIME/./}; echo $((t / 1000)); }

section() { printf '\n== %s\n' "$1"; }

section "환경"
bash --version | head -1
timeout --version | head -1

section "1. 이름과 번호 — kill -l"
echo "\$ kill -l 15 9 1";  kill -l 15 9 1
echo "\$ kill -l TERM";    kill -l TERM
echo "\$ kill -l 143";     kill -l 143
for name in HUP INT QUIT KILL TERM USR1 STOP CONT CHLD; do printf '   %-5s %s\n' "$name" "$(kill -l "$name")"; done

section "2. 아무 시그널도 안 적으면 TERM"
sleep 30 & pid=$!; settle
kill "$pid"; wait "$pid"; echo "   wait 종료 코드 $? (128+15)"

section "3. 같은 시그널을 쓰는 세 가지 형식"
sleep 30 & a=$!; sleep 30 & b=$!; sleep 30 & c=$!; settle
kill -s TERM "$a"; kill -n 15 "$b"; kill -SIGTERM "$c"
wait "$a"; echo "   kill -s TERM  → $?"
wait "$b"; echo "   kill -n 15    → $?"
wait "$c"; echo "   kill -SIGTERM → $?"

section "4. TERM 은 정리할 기회를 주고, KILL 은 주지 않는다"
worker='touch app.lock; trap "echo \"   [작업] TERM 받음 — 락 파일 지우고 종료\"; rm -f app.lock; exit 0" TERM; while :; do sleep 0.1; done'
bash -c "$worker" & pid=$!; settle
kill -TERM "$pid"; wait "$pid"; echo "   TERM: 종료 코드 $?, 락 파일 $(ls app.lock 2>/dev/null || echo 없음)"
bash -c "$worker" & pid=$!; settle
kill -KILL "$pid"; wait "$pid" 2>/dev/null; echo "   KILL: 종료 코드 $?, 락 파일 $(ls app.lock 2>/dev/null || echo 없음)"
rm -f app.lock

section "5. TERM 을 무시하는 프로세스"
bash -c 'trap "" TERM; while :; do sleep 0.1; done' & pid=$!; settle
kill -TERM "$pid"; settle; echo "   TERM 보낸 뒤: $(alive "$pid")"
kill -KILL "$pid"; wait "$pid" 2>/dev/null; echo "   KILL 보낸 뒤: 종료 코드 $?, $(alive "$pid")"

section "6. KILL 에 trap 을 걸면"
bash -c 'trap "echo \"   [작업] KILL 잡았다\"" KILL; echo "   trap KILL 종료 코드 $?"; trap -p KILL | sed "s/^/   trap -p: /"; while :; do sleep 0.1; done' & pid=$!; settle
kill -KILL "$pid"; wait "$pid" 2>/dev/null; echo "   KILL 보낸 뒤: 종료 코드 $? (trap 은 실행되지 않았다)"

section "7. HUP — 설정 다시 읽기에 쓰는 관례"
echo "level=info" > app.conf
bash -c 'load() { . ./app.conf; echo "   [작업] 설정 읽음: level=$level"; }
         load; trap load HUP; while :; do sleep 0.1; done' & pid=$!; settle
echo "level=debug" > app.conf
kill -HUP "$pid"; settle; echo "   HUP 보낸 뒤: $(alive "$pid")"
kill "$pid"; wait "$pid"
sleep 30 & pid=$!; settle
kill -HUP "$pid"; wait "$pid"; echo "   trap 없는 sleep 에 HUP: 종료 코드 $? (128+1)"

section "8. 포그라운드 명령이 도는 동안 trap 은 미뤄진다"
bash -c 'trap "echo \"   [작업] TERM 처리\"; exit 0" TERM; sleep 3' & pid=$!; settle
start=$(now_ms); kill "$pid"; wait "$pid"; echo "   sleep 3 (포그라운드)  : kill 부터 끝날 때까지 $(( $(now_ms) - start ))ms"
bash -c 'trap "echo \"   [작업] TERM 처리\"; exit 0" TERM; sleep 3 & wait $!' & pid=$!; settle
start=$(now_ms); kill "$pid"; wait "$pid"; echo "   sleep 3 & wait \$!    : kill 부터 끝날 때까지 $(( $(now_ms) - start ))ms"

section "9. 부모만 죽이면 자식은 남는다 — 프로세스 그룹으로 보내기"
set -m   # 작업 제어를 켜면 백그라운드 작업마다 자기 프로세스 그룹을 받는다
bash -c 'sleep 30 & echo $! > child.pid; wait' & parent=$!; settle
child=$(cat child.pid)
kill -TERM "$parent"; wait "$parent" 2>/dev/null
echo "   부모 PID 에만 TERM → 부모 $(alive "$parent") / 자식 $(alive "$child")"
kill "$child" 2>/dev/null
bash -c 'sleep 30 & echo $! > child.pid; wait' & parent=$!; settle
child=$(cat child.pid)
kill -TERM -- "-$parent"; wait "$parent" 2>/dev/null; settle
echo "   -PGID 로 그룹에 TERM → 부모 $(alive "$parent") / 자식 $(alive "$child")"
set +m

section "10. STOP 과 CONT — 멈췄다 이어 가기"
bash -c 'n=0; while :; do n=$((n+1)); echo $n > tick.log; sleep 0.1; done' & pid=$!; settle
kill -STOP "$pid"; sleep 0.2; t1=$(cat tick.log); sleep 1; t2=$(cat tick.log)
echo "   STOP 뒤 1초 동안 카운터: $t1 → $t2 ($(alive "$pid"))"
kill -CONT "$pid"; sleep 1; t3=$(cat tick.log)
echo "   CONT 뒤 1초 동안 카운터: $t2 → $t3"
kill "$pid"; wait "$pid"

section "11. 없는 PID 에 보내면"
kill -0 999999 2>&1 | sed 's/^.*kill:/   kill:/'; echo "   종료 코드 ${PIPESTATUS[0]}"

section "12. timeout — 시간이 지나면 보내기"
timeout 0.5 sleep 5;                     echo "   timeout 0.5 sleep 5                   → $?"
timeout -s KILL 0.5 sleep 5 2>/dev/null; echo "   timeout -s KILL 0.5 sleep 5           → $?"
timeout --preserve-status 0.5 sleep 5;   echo "   timeout --preserve-status 0.5 sleep 5 → $?"
timeout -v 0.5 sleep 5 2>&1 | sed 's/^/   /'
start=$(now_ms)
timeout 0.5 bash -c 'trap "" TERM; sleep 3'
echo "   TERM 무시 작업, -k 없음 → $? ($(( $(now_ms) - start ))ms)"
start=$(now_ms)
timeout -k 1 0.5 bash -c 'trap "" TERM; sleep 3' 2>/dev/null
echo "   TERM 무시 작업, -k 1    → $? ($(( $(now_ms) - start ))ms)"

section "13. 작업 번호로 보내기 — kill %1"
sleep 30 & settle
jobs | sed 's/^/   jobs: /'
kill %1; wait %1; echo "   kill %1 → 종료 코드 $?"

section "14. trap 을 보고 되돌리기 — trap -p, -P, -"
trap 'echo cleanup' TERM
trap -p TERM | sed 's/^/   trap -p TERM: /'
trap -P TERM | sed 's/^/   trap -P TERM: /'
trap - TERM
echo "   trap - TERM 뒤 trap -p TERM: [$(trap -p TERM)]"

rm -f app.lock app.conf child.pid tick.log

#!/usr/bin/env bash
# tail 의 옵션을 갈래별로 돌려 보고, 로그 로테이션 앞에서 -f 와 -F 가 어떻게 갈리는지 확인한다.
# 백그라운드로 띄운 tail 의 출력은 파일로 받아 두었다가 나중에 찍는다.
set -u
exec 2>&1  # tail 의 안내 문구(stderr)도 순서대로 기록에 남긴다

work_dir="$(mktemp -d)"
trap 'cd /; rm -rf "${work_dir}"' EXIT
cd "${work_dir}"

show() {
  echo "\$ $*"
  "$@"
  echo "(종료 코드 $?)"
}

section() {
  echo
  echo "== $* =="
}

echo "tail: $(tail --version | head -n 1)"
echo "grep: $(grep --version | head -n 1)"

section "0. 이 환경 tail 의 옵션 목록 (온라인 매뉴얼과 판이 다를 수 있다)"
tail --help

section "1. 줄 수와 바이트 수 — -n, -n +N, -c, -c +N"
seq -f "line %g" 1 15 > app.log
show tail app.log
show tail -n 3 app.log
show tail -n +13 app.log
show tail -c 8 app.log
show tail -c +80 app.log

section "2. 파일 여러 개 — 머리말과 -q, -v"
printf 'a-1\na-2\n' > a.log
printf 'b-1\nb-2\n' > b.log
show tail -n 1 a.log b.log
show tail -q -n 1 a.log b.log
show tail -v -n 1 a.log

section "3. -z — 줄 구분자를 NUL 로"
printf 'one\0two\0three\0' > nul.dat
echo "\$ tail -z -n 2 nul.dat | tr '\\0' '\\n'"
tail -z -n 2 nul.dat | tr '\0' '\n'

section "4. -f — 늘어나는 내용을 이어서 찍는다"
tail -f -n 0 app.log > follow.out &
follow_pid=$!
sleep 1
echo "appended 16" >> app.log
echo "appended 17" >> app.log
sleep 2
kill "${follow_pid}"; wait "${follow_pid}" 2>/dev/null
echo "[tail -f -n 0 app.log 이 찍은 것]"
cat follow.out

section "5. 이름 바꾸기 로테이션 — -f(descriptor) 대 -F(name)"
seq -f "old %g" 1 3 > svc.log
tail -f -n 0 svc.log > by_descriptor.out 2>&1 &
desc_pid=$!
tail -F -n 0 svc.log > by_name.out 2>&1 &
name_pid=$!
sleep 1
echo "before rotate" >> svc.log
sleep 2
mv svc.log svc.log.1          # logrotate 의 기본 동작: 이름을 바꾸고
: > svc.log                   # 새 파일을 만든다
echo "after rotate 1" >> svc.log
echo "late write to old file" >> svc.log.1   # 아직 옛 파일을 쥔 프로세스가 쓴 줄
for second in 1 2 3 4 5 6 7 8; do
  sleep 1
  if grep -q "after rotate 1" by_name.out; then seen="보임"; else seen="안 보임"; fi
  echo "  로테이션 ${second}초 뒤: -F 출력에 'after rotate 1' ${seen}"
done
echo "after rotate 2" >> svc.log
sleep 2
kill "${desc_pid}" "${name_pid}"; wait 2>/dev/null
echo "[tail -f 최종 출력]"
cat by_descriptor.out
echo "[tail -F 최종 출력]"
cat by_name.out

section "6. --max-unchanged-stats=1 — 이름 확인을 더 자주 한다"
seq -f "old %g" 1 3 > fast.log
tail -F --max-unchanged-stats=1 -n 0 fast.log > fast.out 2>&1 &
fast_pid=$!
sleep 1
mv fast.log fast.log.1
echo "after rotate 1" > fast.log
for second in 1 2 3 4; do
  sleep 1
  if grep -q "after rotate 1" fast.out; then seen="보임"; else seen="안 보임"; fi
  echo "  로테이션 ${second}초 뒤: 'after rotate 1' ${seen}"
done
kill "${fast_pid}"; wait 2>/dev/null
echo "[최종 출력]"
cat fast.out

section "7. copytruncate — 파일을 비우면 -f 는 처음부터 다시 읽는다"
printf 'first line of thirty bytes!!\n' > trunc.log
tail -f -n 0 trunc.log > trunc.out 2>&1 &
trunc_pid=$!
sleep 1
echo "appended before truncate" >> trunc.log
sleep 2
: > trunc.log
echo "after truncate" >> trunc.log
sleep 2
echo "[비운 뒤 짧게 쓴 경우]"
cat trunc.out
# 비운 직후, tail 이 다음에 확인하기 전에 원래보다 길게 쓰면
: > trunc.log
printf 'AAAAAAAAAA-1\nBBBBBBBBBB-2\nCCCCCCCCCC-3\nDDDDDDDDDD-4\nEEEEEEEEEE-5\n' >> trunc.log
sleep 2
kill "${trunc_pid}"; wait 2>/dev/null
echo "[비운 직후 더 길게 쓴 경우까지 포함한 최종 출력]"
cat trunc.out

section "8. 없는 파일 — -f 는 바로 끝나고, -F(--retry) 는 기다린다"
show tail -f missing.log
tail -F -n +1 missing.log > retry.out 2>&1 &
retry_pid=$!
sleep 1
echo "created later" > missing.log
sleep 2
kill "${retry_pid}"; wait 2>/dev/null
echo "[tail -F missing.log 출력]"
cat retry.out

section "9. --pid — 지정한 프로세스가 끝나면 tail 도 끝난다"
sleep 3 &
writer_pid=$!
SECONDS=0
tail -f -n 0 --pid="${writer_pid}" app.log
echo "tail 종료 코드 $?, 걸린 시간 약 ${SECONDS}초 (sleep 3 이 끝난 뒤)"

section "10. -s — 확인 간격"
printf '' > slow.log
tail -f -s 4 -n 0 slow.log > slow.out &
slow_pid=$!
sleep 1
echo "written at 1s" >> slow.log
sleep 1
echo "[쓴 지 1초 뒤] $(cat slow.out)"
sleep 3
echo "[쓴 지 4초 뒤] $(cat slow.out)"
kill "${slow_pid}"; wait 2>/dev/null

section "11. 파이프 뒤 grep 의 버퍼 — 파일로 받으면 줄이 바로 안 나온다"
printf '' > pipe.log
sleep 5 &
keeper_pid=$!   # 이 프로세스가 끝나면 --pid 로 두 tail 이 끝나고, 파이프가 닫힌다
tail -f -n 0 --pid="${keeper_pid}" pipe.log | grep ERROR > grep_plain.out &
tail -f -n 0 --pid="${keeper_pid}" pipe.log | grep --line-buffered ERROR > grep_line.out &
sleep 1
echo "ERROR disk full" >> pipe.log
sleep 2
echo "[3초 시점 grep ERROR > 파일]                 $(wc -c < grep_plain.out)바이트"
echo "[3초 시점 grep --line-buffered ERROR > 파일] $(wc -c < grep_line.out)바이트: $(cat grep_line.out)"
wait
echo "[tail 이 끝난 뒤 grep ERROR > 파일]          $(wc -c < grep_plain.out)바이트: $(cat grep_plain.out)"

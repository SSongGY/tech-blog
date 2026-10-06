#!/usr/bin/env bash
# 설정 파일을 고치기 전후를 diff 로 남기고 patch 로 다시 적용·되돌리는 과정을 옵션별로 돌려 본다.
# 작업 폴더를 만들어 그 안에서만 고치고, 끝나면 지운다.
set -u
# diff | head 처럼 파이프를 거쳐도 diff 의 종료 코드가 찍히게 한다
set -o pipefail

work_dir="diff_work"
# diff -u 머리줄에 수정 시각이 찍히므로, 돌릴 때마다 같은 출력이 나오게 시각을 고정한다
fixed_old="2026-10-06 09:00:00"
fixed_new="2026-10-06 09:30:00"

chapter() {
    printf '\n===== %s\n' "$1"
}

run() {
    printf '$ %s\n' "$1"
    # 에러 메시지도 그 명령 바로 아래에 보이게 합치고, 종료 코드는 0이어도 찍는다.
    # diff 는 1(다름)을 정상 결과로 돌려주므로 코드 자체가 이 글의 내용이다.
    eval "$1" 2>&1
    printf '(종료 코드 %d)\n' "$?"
}

make_files() {
    rm -rf "${work_dir}"
    mkdir -p "${work_dir}"
    cd "${work_dir}" || exit 1

    cat > app.conf.orig <<'EOF'
# app server config
listen_port=8080
worker_count=4
db.host=10.0.0.1
db.port=5432
db.pool_size=20
cache.enabled=true
cache.ttl_sec=300
log.level=info
log.dir=/var/log/app
EOF
    # 운영 중 바꾼 것: 워커 수, 커넥션 풀, 로그 레벨
    sed -e 's/^worker_count=4$/worker_count=8/' \
        -e 's/^db.pool_size=20$/db.pool_size=40/' \
        -e 's/^log.level=info$/log.level=debug/' app.conf.orig > app.conf
    touch -d "${fixed_old}" app.conf.orig
    touch -d "${fixed_new}" app.conf
}

make_files

chapter "0. 버전"
run "diff --version | head -1"
run "patch --version | head -1"
run "bash --version | head -1"

chapter "1. 바꾸기 전과 후"
run "cat -n app.conf.orig"
run "cat -n app.conf"

chapter "2. 출력 형식 — 기본(normal)"
run "diff app.conf.orig app.conf"

chapter "3. 통합 형식 -u, 문맥 줄 수 -U"
run "diff -u app.conf.orig app.conf"
run "diff -U1 app.conf.orig app.conf"
run "diff -U0 app.conf.orig app.conf"

chapter "4. 문맥 형식 -c"
run "diff -c app.conf.orig app.conf"

chapter "5. 나란히 -y, 폭 -W, 같은 줄 숨기기"
run "diff -y -W 60 app.conf.orig app.conf"
run "diff -y -W 60 --suppress-common-lines app.conf.orig app.conf"
run "diff -y -W 60 --left-column app.conf.orig app.conf"

chapter "6. 다른지만 -q, 같을 때도 알리기 -s, 종료 코드"
cp app.conf.orig same.conf
run "diff -q app.conf.orig app.conf"
run "diff -s app.conf.orig same.conf"
run "diff app.conf.orig same.conf"
run "diff app.conf.orig no_such.conf"

chapter "7. 머리줄 이름 바꾸기 --label"
run "diff -u --label a/app.conf --label b/app.conf app.conf.orig app.conf"

chapter "8. 공백·대소문자·빈 줄·특정 줄 무시"
# 줄마다 다른 종류의 차이를 하나씩 넣었다: 공백 삽입, 공백 양, 줄 끝 공백, 빈 줄, 대소문자, 주석 날짜
printf 'listen_port=8080\nworker_count = 4\ndb.host=10.0.0.1\nlog.level=info\n# edited 2026-10-01\n' > ws_old.conf
printf 'listen_port = 8080\nworker_count   =   4\n\ndb.host=10.0.0.1   \nLOG.LEVEL=info\n# edited 2026-10-06\n' > ws_new.conf
run "cat -A ws_old.conf"
run "cat -A ws_new.conf"
run "diff ws_old.conf ws_new.conf"
run "diff -Z ws_old.conf ws_new.conf"
run "diff -b ws_old.conf ws_new.conf"
run "diff -w ws_old.conf ws_new.conf"
run "diff -w -B ws_old.conf ws_new.conf"
run "diff -w -B -i ws_old.conf ws_new.conf"
run "diff -w -B -i -I '^# edited' ws_old.conf ws_new.conf"
printf 'a\tb\n' > tab_old.txt
printf 'a       b\n' > tab_new.txt
run "diff tab_old.txt tab_new.txt"
run "diff -E tab_old.txt tab_new.txt"

chapter "9. 윈도에서 저장한 CRLF 파일"
sed 's/$/\r/' app.conf.orig > app_crlf.conf
run "diff -q app.conf.orig app_crlf.conf"
run "diff app.conf.orig app_crlf.conf | head -4 | cat -A"
run "diff --strip-trailing-cr app.conf.orig app_crlf.conf"

chapter "10. 바뀐 곳이 속한 절을 머리줄에 -F"
printf '[server]\nlisten_port=8080\nworker_count=4\nthread_stack_kb=512\nkeepalive_sec=60\n\n[db]\nhost=10.0.0.1\nport=5432\npool_size=20\ntimeout_sec=5\n' > ini_old.conf
sed 's/^pool_size=20$/pool_size=40/' ini_old.conf > ini_new.conf
run "diff -U1 ini_old.conf ini_new.conf | tail -n +3"
run "diff -U1 -F '^\\[' ini_old.conf ini_new.conf | tail -n +3"

chapter "11. 디렉터리 비교 -r, 없는 파일 -N, 제외 -x"
mkdir -p conf_old conf_new
cp app.conf.orig conf_old/app.conf
cp app.conf conf_new/app.conf
printf 'level=info\n' > conf_old/log.conf
printf 'level=info\n' > conf_new/log.conf
printf 'max_conn=100\n' > conf_new/limits.conf
printf 'stale\n' > conf_new/app.conf.bak
touch -d "${fixed_old}" conf_old/*
touch -d "${fixed_new}" conf_new/*
run "diff -rq conf_old conf_new"
run "diff -rq -x '*.bak' conf_old conf_new"
run "diff -ruN -x '*.bak' conf_old conf_new | grep -E '^(diff|---|\\+\\+\\+|@@)'"
run "diff -q --from-file=app.conf.orig app.conf same.conf"

chapter "12. 기계가 읽는 형식 -e, -n"
run "diff -e app.conf.orig app.conf"
run "diff -n app.conf.orig app.conf"

chapter "13. 줄 서식 지정 --LTYPE-line-format, -D"
run "diff --unchanged-line-format= --old-line-format='- %L' --new-line-format='+ %L' app.conf.orig app.conf"
run "diff --unchanged-line-format= --old-line-format= --new-line-format='%dn: %L' app.conf.orig app.conf"
run "diff -D NEW_CONF app.conf.orig app.conf | head -8"

chapter "14. 바이너리 판정 -a"
printf 'key=1\n\000tail\n' > bin_old.dat
printf 'key=2\n\000tail\n' > bin_new.dat
run "diff bin_old.dat bin_new.dat"
run "diff -a bin_old.dat bin_new.dat | cat -v"

chapter "15. 탭 표시 -t, -T, --tabsize, 계산 방법 -d"
run "diff -T tab_old.txt tab_new.txt | cat -A"
run "diff -t --tabsize=4 tab_old.txt tab_new.txt | cat -A"
run "diff -d -u app.conf.orig app.conf | tail -n +3"

chapter "16. patch — 만들고, 미리 보고, 적용하고, 되돌린다"
diff -u app.conf.orig app.conf > app.conf.patch
cp app.conf.orig target.conf
run "patch --dry-run target.conf app.conf.patch"
run "cmp target.conf app.conf.orig && echo '미리보기 뒤에도 원본 그대로'"
run "patch target.conf app.conf.patch"
run "cmp target.conf app.conf && echo '적용 결과가 app.conf 와 같다'"
run "patch -R target.conf app.conf.patch"
run "cmp target.conf app.conf.orig && echo '되돌린 결과가 원본과 같다'"

chapter "17. 이미 적용된 패치를 또 적용하면 — -N, -t, -f"
cp app.conf target.conf
run "patch target.conf app.conf.patch < /dev/null"
run "cat target.conf.rej 2>/dev/null | head -3; rm -f target.conf.rej target.conf.orig"
cp app.conf target.conf
run "patch -N target.conf app.conf.patch"
run "rm -f target.conf.rej; patch -t target.conf app.conf.patch"
run "cmp target.conf app.conf.orig && echo '-t 는 뒤집어 적용했다 → 원본으로 돌아감'"
cp app.conf target.conf
run "patch -f target.conf app.conf.patch"
run "ls target.conf*; rm -f target.conf.rej target.conf.orig"

chapter "18. 대상이 조금 달라졌을 때 — offset, fuzz, -F, .rej, --merge"
{ printf '# managed by ops\n# do not edit\n'; cat app.conf.orig; } > shifted.conf
run "patch shifted.conf app.conf.patch"
run "ls shifted.conf*"
# 덩어리의 맨 앞 문맥 줄만 바뀐 경우 — fuzz 가 그 줄을 건너뛴다
sed 's/^# app server config$/# app server config (prod)/' app.conf.orig > fuzzy.conf
cp fuzzy.conf fuzzy2.conf
run "patch fuzzy.conf app.conf.patch"
run "ls fuzzy.conf*"
run "patch -F0 fuzzy2.conf app.conf.patch"
run "ls fuzzy2.conf*"
# 덩어리 한가운데의 문맥 줄이 바뀐 경우 — fuzz 로는 못 넘는다
sed 's/^db.port=5432$/db.port=6432/' app.conf.orig > inner.conf
cp inner.conf inner2.conf
run "patch inner.conf app.conf.patch"
run "patch --merge inner2.conf app.conf.patch"
run "cat inner2.conf"
# 바꾸려는 줄 자체가 이미 다른 값 — 진짜 충돌
sed 's/^db.pool_size=20$/db.pool_size=30/' app.conf.orig > conflict.conf
run "patch -r conflict.rej --reject-format=context conflict.conf app.conf.patch"
run "cat conflict.rej"

chapter "19. 결과를 다른 파일로 -o, 백업 -b -z -V"
run "patch -o out.conf app.conf.orig app.conf.patch && cmp out.conf app.conf && echo '원본은 그대로, 결과는 out.conf'"
cp app.conf.orig backup.conf
run "patch -b -z .before backup.conf app.conf.patch"
run "patch -R -b -V numbered backup.conf app.conf.patch"
run "ls backup.conf*"

chapter "20. 디렉터리 패치 -p, -d, -i, -E"
cp -r conf_old live
rm -f conf_new/app.conf.bak
printf '' > conf_new/log.conf
diff -ruN conf_old conf_new > dir.patch
run "head -3 dir.patch"
run "patch -d live -p0 -i ../dir.patch --dry-run"
run "patch -d live -p1 -i ../dir.patch"
run "ls live"
cp -r conf_old live2
run "patch -d live2 -p1 -E -s -i ../dir.patch"
run "ls live2"
run "patch -d live2 -p1 -R --verbose -i ../dir.patch | grep -v '^|'"
run "ls live2"

chapter "21. 공백만 다른 대상 -l"
sed 's/^worker_count=4$/worker_count=4  /' app.conf.orig > spaced.conf
cp spaced.conf spaced2.conf
run "patch -F0 spaced.conf app.conf.patch"
run "patch -F0 -l spaced2.conf app.conf.patch"

cd .. || exit 1
rm -rf "${work_dir}"

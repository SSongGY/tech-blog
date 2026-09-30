#!/usr/bin/env bash
# GNU tar 1.35 와 gzip 1.14 의 자주 쓰는 옵션을 갈래별로 돌려 본다.
# 모든 파일은 /tmp/tardemo 아래에만 만들고 끝나면 지운다.

work=/tmp/tardemo
rm -rf "$work"
mkdir -p "$work"
cd "$work" || exit 1
trap 'cd / && rm -rf "$work"' EXIT

# 명령을 찍고 돌린다. 실패하면 종료 코드를 따로 적는다 — 성공·실패가 출력에서 보여야 한다
run() {
    echo "\$ $1"
    eval "$1" 2>&1
    local rc=$?
    [ "$rc" -ne 0 ] && echo "[종료 코드 $rc]"
    return 0
}

section() { echo; echo "== $1 =="; }

# 기본 데이터: 앱 폴더 하나
make_app() {
    rm -rf app
    mkdir -p app/conf app/logs app/.git
    printf 'port=8080\n' > app/conf/app.conf
    printf 'line1\nline2\n' > app/logs/a.log
    printf 'ref\n' > app/.git/HEAD
    seq 1 20000 > app/data.txt
    touch -d '2026-01-01 00:00:00' app/conf/app.conf app/logs/a.log app/.git/HEAD app/data.txt
}

section "0. 버전과 압축 프로그램"
run 'tar --version | head -n 1'
run 'gzip --version | head -n 1'
for prog in gzip bzip2 xz zstd lzip lzop compress; do
    if command -v "$prog" >/dev/null; then echo "  $prog 있음"; else echo "  $prog 없음"; fi
done
run 'tar --show-defaults'

make_app

section "1. 동작 모드 — 하나만 고른다"
run 'tar -cf app.tar app'
run 'tar -tf app.tar'
# 목록의 소유자 칸에 이 PC 계정 이름이 찍히므로 번호로 찍는다
run 'tar --numeric-owner -tvf app.tar app/conf/app.conf'
cp app.tar m.tar
printf 'new\n' > extra.txt
run 'tar -rf m.tar extra.txt && tar -tf m.tar | tail -n 1'
run 'tar -uf m.tar extra.txt && tar -tf m.tar | grep extra.txt | wc -l'
touch -d '2027-01-01' extra.txt
run 'tar -uf m.tar extra.txt && tar -tf m.tar | grep extra.txt | wc -l'
run 'tar --delete -f m.tar extra.txt && tar -tf m.tar | grep extra.txt | wc -l'
run 'tar -cf other.tar extra.txt && tar -Af m.tar other.tar && tar -tf m.tar | tail -n 1'
run 'tar -cx -f m.tar'

section "2. 옵션 쓰는 법 세 가지와 -f 의 자리"
run 'tar cvf style1.tar app/conf'
run 'tar -cvf style2.tar app/conf'
run 'tar --create --verbose --file=style3.tar app/conf'
run 'tar -cfv style4.tar app/conf'
run 'ls v style4.tar'
run 'tar -tf v'
run 'tar -cf style5.tar -v app/conf'

section "3. 압축 — 만들 때 고르고, 읽을 때는 알아서"
run 'tar -czf app.tar.gz app'
run 'tar -cjf app.tar.bz2 app'
run 'tar -cJf app.tar.xz app'
run 'tar --zstd -cf app.tar.zst app'
run 'tar -caf auto.tar.gz app && gzip -l auto.tar.gz'
run 'tar -caf auto.tar.xz app && tar -tf auto.tar.xz | head -n 1'
run 'tar -cf fake.tar.gz app && gzip -t fake.tar.gz'
run 'tar -tf app.tar.gz | head -n 2'
run 'tar -tzf app.tar'
run 'tar -I "gzip -9" -cf best.tar.gz app'
run 'wc -c app.tar app.tar.gz best.tar.gz app.tar.bz2 app.tar.xz | head -n 5'
run 'cat app.tar.gz | tar -tzf - | head -n 1'

section "4. 절대경로 — 만들 때 / 를 떼고, -P 는 붙인 채 둔다"
mkdir -p "$work/etc-sample"
printf 'secret=old\n' > "$work/etc-sample/app.conf"
run "tar -cf abs.tar $work/etc-sample/app.conf"
run 'tar -tf abs.tar'
run "tar -cPf abs-p.tar $work/etc-sample/app.conf"
run 'tar -tf abs-p.tar'
printf 'secret=CHANGED\n' > "$work/etc-sample/app.conf"
mkdir -p unpack1 && cd unpack1 || exit 1
run 'tar -xf ../abs-p.tar'
run "cat $work/etc-sample/app.conf"
run 'find . -type f'
run 'tar -xPf ../abs-p.tar'
run "cat $work/etc-sample/app.conf"
cd "$work" || exit 1

section "5. 위로 올라가는 이름(../) — 풀 때 막는다"
mkdir -p inner && printf 'escaped\n' > outside.txt
cd inner || exit 1
run 'tar -cPf ../dotdot.tar ../outside.txt'
cd "$work" || exit 1
run 'tar -tf dotdot.tar'
rm -f outside.txt
mkdir -p unpack2 && cd unpack2 || exit 1
run 'tar -xf ../dotdot.tar'
run 'ls ../outside.txt'
run 'tar -xPf ../dotdot.tar && cat ../outside.txt'
cd "$work" || exit 1
rm -f outside.txt

section "6. 풀기 전에 목록부터 — 절대경로와 ../ 를 찾는다"
run "tar -tf abs-p.tar | grep -E '^/|(^|/)\\.\\.(/|\$)'"
run "tar -tf dotdot.tar | grep -E '^/|(^|/)\\.\\.(/|\$)'"
run "tar -tf app.tar | grep -E '^/|(^|/)\\.\\.(/|\$)' || echo '(해당 없음)'"

section "7. 풀 위치와 이름 바꾸기"
run 'mkdir -p out && tar -xf app.tar -C out && find out -name app.conf'
run 'mkdir -p strip && tar -xf app.tar -C strip --strip-components=1 && ls strip'
run 'mkdir -p xform && tar -xf app.tar -C xform --transform="s,^app/,myapp/," && ls xform'
run 'tar -tf app.tar --transform="s,^app/,myapp/," --show-transformed-names | head -n 3'
run 'mkdir -p xform2 && tar -xf app.tar -C xform2 --transform="s,^app\(/\|$\),myapp\1," && ls xform2'
run 'mkdir -p one && tar -xf style2.tar -C one --one-top-level=bundle && find one -type f'
run 'mkdir -p pick && tar -xf app.tar -C pick app/conf/app.conf && find pick -type f'
run 'tar -xf app.tar -C pick "app/logs/*.log"'
run 'tar -xf app.tar -C pick --wildcards "app/logs/*.log" && find pick -name "*.log"'
run 'tar -xOf app.tar app/conf/app.conf'
run 'tar -xf app.tar --to-command="wc -l" app/logs/a.log'

section "8. 덮어쓰기 — 기본은 덮는다"
mkdir -p ow && tar -xf app.tar -C ow
printf 'port=9090\n' > ow/app/conf/app.conf
run 'tar -xf app.tar -C ow && cat ow/app/conf/app.conf'
printf 'port=9090\n' > ow/app/conf/app.conf
run 'tar -xkf app.tar -C ow'
run 'cat ow/app/conf/app.conf'
run 'tar -xf app.tar -C ow --skip-old-files && cat ow/app/conf/app.conf'
touch -d '2027-06-01' ow/app/conf/app.conf
run 'tar -xf app.tar -C ow --keep-newer-files && cat ow/app/conf/app.conf'
run 'tar -xf app.tar -C ow --backup=numbered && ls ow/app/conf'

section "9. 담을 파일 고르기"
run 'tar -cf ex1.tar --exclude="*.log" app && tar -tf ex1.tar'
run 'tar -cf ex2.tar --exclude-vcs app && tar -tf ex2.tar'
printf 'app/conf/app.conf\napp/data.txt\n' > list.txt
run 'tar -cf fromlist.tar -T list.txt && tar -tf fromlist.tar'
run 'find app -name "*.conf" -print0 | tar -cf null.tar --null -T - && tar -tf null.tar'
run 'tar -cf norec.tar --no-recursion app app/conf && tar -tf norec.tar'
touch -d '2026-06-01' app/logs/a.log
run 'tar -cf newer.tar -N "2026-03-01" app 2>/dev/null; tar -tf newer.tar | grep -v "/$"'
run 'tar -cf newer2.tar --newer-mtime="2026-03-01" app 2>/dev/null; tar -tf newer2.tar | grep -v "/$"'
run 'stat -c "%n  mtime=%y  ctime=%z" app/conf/app.conf | cut -c1-90'
run 'tar -cf rm.tar --remove-files extra.txt && ls extra.txt'

section "10. 같은 내용이면 같은 아카이브 — 재현 가능한 묶음"
run 'tar -cf r1.tar app && sleep 1 && touch app && tar -cf r2.tar app && cmp -s r1.tar r2.tar && echo same || echo differ'
REPRO='--sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner'
run "tar $REPRO -cf r3.tar app && sleep 1 && touch app && tar $REPRO -cf r4.tar app && cmp -s r3.tar r4.tar && echo same || echo differ"
run "tar $REPRO -czf g1.tar.gz app && sleep 1 && tar $REPRO -czf g2.tar.gz app && cmp -s g1.tar.gz g2.tar.gz && echo same || echo differ"
run 'tar -tvf r3.tar app/data.txt'
run 'tar --numeric-owner -tvf app.tar app/data.txt'
run 'tar --utc -tvf r3.tar app/data.txt'

section "11. 검사 — 비교, 검증, 증분"
make_app
run 'tar -df app.tar'
printf 'port=1\n' > app/conf/app.conf
run 'tar -df app.tar'
run 'tar -cWf verify.tar app/logs && echo verified'
make_app
run 'tar -cf lvl0.tar -g snap.db app && tar -tf lvl0.tar | wc -l'
printf 'added\n' > app/logs/b.log
run 'tar -cf lvl1.tar -g snap.db app && tar -tf lvl1.tar | grep -v "/$"'

section "12. 진행 상황과 합계"
run 'tar -cf big.tar --totals app'
run 'tar -cf big.tar --checkpoint=4 --checkpoint-action=echo="checkpoint #%u" app'
run 'tar -tRf app.tar app/conf/app.conf'
run 'tar --numeric-owner --full-time -tvf app.tar app/conf/app.conf'
run 'tar -cf idx.tar -v --index-file=idx.txt app/conf && cat idx.txt'
run 'tar -tf nosuch.tar'
run 'tar -xf app.tar no/such/member'

section "13. gzip 단독 — 기본은 원본을 지운다"
seq 1 50000 > g.txt
run 'gzip g.txt && ls g.txt*'
run 'gzip -d g.txt.gz && ls g.txt*'
run 'gzip -k g.txt && ls g.txt*'
run 'gzip g.txt'
run 'gzip -f g.txt && ls g.txt*'
run 'gzip -l g.txt.gz'
run 'gzip -t g.txt.gz && echo ok'
run 'gzip -cd g.txt.gz | tail -n 1'
run 'gzip -dc g.txt.gz | gzip -1 > seq1.gz && gzip -dc g.txt.gz | gzip -9 > seq9.gz && wc -c seq1.gz seq9.gz'
tar --help > help.txt
run 'gzip -1 -c help.txt > help1.gz && gzip -6 -c help.txt > help6.gz && gzip -9 -c help.txt > help9.gz && wc -c help.txt help1.gz help6.gz help9.gz'
run 'gzip -dk g.txt.gz && ls g.txt*'
run 'rm g.txt.gz && gzip -S .z g.txt && ls g.txt*'
run 'gzip -dv -S .z g.txt.z && ls g.txt*'
cp g.txt orig.txt
run 'gzip -c orig.txt > renamed.gz && gzip -lN renamed.gz'
rm -f orig.txt
run 'gzip -dN renamed.gz && ls orig.txt renamed* 2>&1'
run 'gzip -n -c g.txt > noname.gz && gzip -lN noname.gz'
run 'gzip -c g.txt > a.gz && sleep 1 && touch g.txt && gzip -c g.txt > b.gz && cmp -s a.gz b.gz && echo same || echo differ'
run 'gzip -nc g.txt > a.gz && sleep 1 && touch g.txt && gzip -nc g.txt > b.gz && cmp -s a.gz b.gz && echo same || echo differ'
mkdir -p tree/sub && seq 1 100 > tree/a.txt && seq 1 100 > tree/sub/b.txt
run 'gzip -r tree && find tree -type f | sort'
run 'gzip -dr tree && find tree -type f | sort'
printf 'broken' > bad.gz
run 'gzip -t bad.gz'
run 'gzip -tq bad.gz'
run 'gzip -dc app.tar.gz | tar -tf - | head -n 1'

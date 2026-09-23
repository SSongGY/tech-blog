#!/usr/bin/env bash
# sed 로 설정 파일을 일괄 치환하기 전에 확인할 것들을 실제로 돌려 본다.
# 작업 폴더를 만들어 그 안에서만 고치고, 끝나면 지운다.
set -u

work_dir="sed_work"

make_files() {
    rm -rf "${work_dir}"
    mkdir -p "${work_dir}"
    cd "${work_dir}" || exit 1

    # 10.0.0.1 만 10.0.0.2 로 옮기려 한다. 12 와 100 은 다른 서버고,
    # cache.bytes 는 IP 가 아니지만 점을 이스케이프하지 않은 정규식에 걸린다.
    cat > app.conf <<'EOF'
# primary: 10.0.0.1
db.host=10.0.0.1
db.replica=10.0.0.12
backup.host=10.0.0.100
cache.bytes=10000001
log.dir=/var/log/app
EOF

    cat > batch.conf <<'EOF'
db.host=10.0.0.1
db.pool=20
EOF

    # 윈도우에서 편집해 CRLF 줄끝이 된 파일
    printf 'db.host=10.0.0.1\r\ndb.pool=20\r\n' > crlf.conf
}

chapter() {
    printf '\n===== %s\n' "$1"
}

run() {
    printf '$ %s\n' "$1"
    # 에러 메시지도 그 명령 바로 아래에 보이도록 합친다
    eval "$1" 2>&1
    local rc=$?
    if [ "${rc}" -ne 0 ]; then
        printf '(종료 코드 %d)\n' "${rc}"
    fi
}

make_files

chapter "0. 버전"
run "sed --version | head -1"
run "bash --version | head -1"

chapter "1. 바꾸기 전 — 파일 내용"
run "cat -n app.conf"

chapter "2. 흔히 치는 명령을 미리보기로 돌린다 (-n + p 플래그: 바뀐 줄만 찍기)"
run "sed -n 's/10.0.0.1/10.0.0.2/gp' app.conf"

chapter "3. 점만 이스케이프하면 — cache.bytes 는 빠지지만 12 와 100 이 여전히 걸린다"
run "sed -n 's/10\.0\.0\.1/10.0.0.2/gp' app.conf"

chapter "4. 점을 이스케이프하고 경계를 건다"
run "sed -n 's/\b10\.0\.0\.1\b/10.0.0.2/gp' app.conf"
run "sed -n 's/=10\.0\.0\.1\$/=10.0.0.2/p' app.conf"

chapter "5. 파일 전체를 diff 로 미리 본다"
run "sed 's/=10\.0\.0\.1\$/=10.0.0.2/' app.conf | diff -u app.conf - | tail -n +3"

chapter "6. 치환이 한 건도 없어도 sed 는 0 을 돌려준다"
run "sed -n 's/=10\.9\.9\.9\$/=10.0.0.2/p' app.conf; echo \"종료 코드 \$?\""
run "grep -c '=10\.9\.9\.9\$' app.conf"

chapter "7. -i.bak — 백업을 남기고 고친 뒤 diff"
run "sed -i.bak 's/=10\.0\.0\.1\$/=10.0.0.2/' app.conf"
run "ls app.conf*"
run "diff app.conf.bak app.conf"

chapter "8. -i 접미사에 * 를 쓰면 파일 이름 자리에 들어간다"
run "sed -i'orig_*' 's/db.pool=20/db.pool=40/' batch.conf"
run "ls orig_* batch.conf"

chapter "9. -i 는 새 파일을 만든다 — 하드 링크가 끊긴다"
run "ln batch.conf batch.link"
run "stat -c '%h %n' batch.conf batch.link"
run "sed -i 's/db.pool=40/db.pool=60/' batch.conf"
run "stat -c '%h %n' batch.conf batch.link"
run "grep pool batch.conf batch.link"

chapter "10. 여러 파일 — \$ 주소는 기본이 이어 붙인 한 흐름, -s 면 파일마다"
run "sed -n '\$p' app.conf batch.conf"
run "sed -s -n '\$p' app.conf batch.conf"
run "sed -n '1p' app.conf batch.conf"
run "sed -s -n '1p' app.conf batch.conf"

chapter "11. BRE 와 ERE (-E)"
run "sed -n 's/\(db\)\.\([a-z]*\)=/\1_\2: /p' app.conf"
run "sed -E -n 's/(db)\.([a-z]+)=/\1_\2: /p' app.conf"
run "echo 'a+b' | sed 's/a+/X/'"
run "echo 'aaab' | sed -E 's/a+/X/'"

chapter "12. 구분자를 바꾼다 — 경로에 / 가 들어 있을 때"
run "sed -n 's|/var/log/app|/data/log/app|p' app.conf"

chapter "13. -e 여러 개와 -f 스크립트 파일"
run "sed -e 's/db.host/DB_HOST/' -e '/^#/d' app.conf"
printf 's/db.host/DB_HOST/\n/^#/d\n' > rename.sed
run "cat rename.sed"
run "sed -f rename.sed app.conf"

chapter "14. 주소 — 줄 번호, 범위, 정규식, 부정, 단계, 0,/re/"
run "sed -n '2,3p' app.conf"
run "sed -n '/replica/,\$p' app.conf"
run "sed '/^#/!s/10\.0\.0/192.168.0/' app.conf"
run "sed -n '1~2p' app.conf"
run "printf 'x=1\nx=2\nx=3\n' | sed '0,/x=/s//y=/'"
run "printf 'x=1\nx=2\nx=3\n' | sed '1,/x=/s/x=/y=/'"

chapter "15. s 명령 플래그 — g, 숫자, I, w"
run "echo 'a-a-a-a' | sed 's/a/X/'"
run "echo 'a-a-a-a' | sed 's/a/X/3'"
run "echo 'a-a-a-a' | sed 's/a/X/2g'"
run "echo 'DB.HOST=1' | sed 's/db\.host/db.host/I'"
run "sed -n 's/10\.0\.0/192.168.0/w changed.txt' app.conf"
run "cat changed.txt"

chapter "16. 줄 단위 명령 — d, a, i, c, y, q"
run "sed '/^#/d' app.conf"
run "sed '/^db.host/a db.timeout=5' app.conf"
run "sed '/^db.host/i # 2026-09-23 이전' app.conf"
run "sed '/^log.dir/c log.dir=/data/log' app.conf"
run "echo 'db.host' | sed 'y/abcdefghijklmnopqrstuvwxyz/ABCDEFGHIJKLMNOPQRSTUVWXYZ/'"
run "sed '/replica/q' app.conf"
run "sed '/replica/q5' app.conf > /dev/null; echo \"종료 코드 \$?\""

chapter "17. -z — 줄 경계를 넘는 치환"
run "sed -z 's/\n/,/g' batch.conf; echo"

chapter "18. CRLF 파일 — -b 로 열면 리눅스와 같이 \\r 이 보인다"
run "sed -n 'l' crlf.conf"
run "sed -b -n 'l' crlf.conf"
run "sed -b -n 's/=20\$/=40/p' crlf.conf"
run "sed -b -n 's/=20\r\$/=40\r/p' crlf.conf | od -c | head -2"

chapter "19. -l — l 명령의 줄 바꿈 폭"
run "echo 'db.host=10.0.0.1;db.pool=20' | sed -n -l 12 'l'"

chapter "20. --sandbox — w·r·e 명령을 막는다"
run "sed --sandbox -n 's/10/20/w out.txt' app.conf"

chapter "21. --posix — GNU 확장을 끈다"
run "echo 'aaab' | sed 's/a\+/X/'"
run "echo 'aaab' | sed --posix 's/a\+/X/'"

chapter "22. --debug — 스크립트를 어떻게 읽었는지 보여 준다"
run "echo 'db.host=10.0.0.1' | sed --debug 's/=10\.0\.0\.1\$/=10.0.0.2/'"

chapter "23. -i 와 접미사 사이에 공백을 넣으면"
run "sed -i .bak 's/db.pool=60/db.pool=70/' batch.conf"

chapter "24. 링크를 유지하며 고치기 — 원본에 덮어쓴다"
run "stat -c '%h %n' batch.conf"
run "ln batch.conf batch.link2"
run "sed 's/db.pool=60/db.pool=80/' batch.conf > batch.tmp && cat batch.tmp > batch.conf && rm batch.tmp"
run "stat -c '%h %n' batch.conf batch.link2"
run "grep pool batch.conf batch.link2"

chapter "25. -i 없이 여러 파일에 1i — 첫 파일에만 들어간다"
run "sed '1i # managed' app.conf batch.conf"

cd .. || exit 1
rm -rf "${work_dir}"

#!/usr/bin/env bash
# ssh_config 가 실제로 어떻게 풀리는지 ssh -G 로 확인한다.
#
# 접속은 한 번도 하지 않는다. -G 는 설정을 해석해 최종값만 찍고 끝내는 옵션이라
# 서버가 없어도 "이 별칭이 어떤 값으로 풀리는가"를 전부 확인할 수 있다.
set -u

cd "$(dirname "$0")"
work="probe_work"            # probe* 는 gitignore 된다. 매 실행마다 다시 만든다
rm -rf "$work"
mkdir -p "$work/conf.d"
work_abs=$(pwd)/$work

rule() { printf '\n==== %s\n' "$1"; }

# ssh -G 는 설정값을 한 줄에 하나씩 찍는다. 볼 키워드만 골라 낸다.
resolve() {
    local conf=$1 target=$2
    shift 2
    local keys
    keys=$(printf '%s|' "$@")
    ssh -T -G -F "$conf" "$target" 2>&1 | grep -E "^(${keys%|}) "
}

show_conf() {
    printf -- '-- %s\n' "$1"
    sed 's/^/   /' "$1"
}

rule "환경"
ssh -V 2>&1          # ssh -V 는 표준에러로 찍는다
printf 'bash %s\n' "${BASH_VERSION}"

# ---------------------------------------------------------------- 1. 별칭
cat > "$work/alias.conf" <<'CFG'
Host web
    HostName 203.0.113.10
    User admin
    Port 2222
    ServerAliveInterval 60
    ServerAliveCountMax 3
CFG

rule "1. 호스트 별칭 — 별칭 하나가 네 가지 값으로 풀린다"
show_conf "$work/alias.conf"
printf -- '-- ssh -G -F alias.conf web\n'
resolve "$work/alias.conf" web user hostname port serveraliveinterval serveralivecountmax

printf -- '\n-- HostName 을 안 적은 별칭은 별칭 자체가 호스트명이 된다\n'
resolve "$work/alias.conf" nowhere hostname port

# ---------------------------------------------------- 2. 먼저 읽힌 값이 이긴다
cat > "$work/order-top.conf" <<'CFG'
Host *
    User deploy

Host web
    User admin
CFG

cat > "$work/order-bottom.conf" <<'CFG'
Host web
    User admin

Host *
    User deploy
CFG

rule "2. 같은 키워드가 두 번 나오면 — 먼저 읽힌 값이 이긴다"
show_conf "$work/order-top.conf"
printf -- '-- ssh -G -F order-top.conf web\n'
resolve "$work/order-top.conf" web user
show_conf "$work/order-bottom.conf"
printf -- '-- ssh -G -F order-bottom.conf web\n'
resolve "$work/order-bottom.conf" web user

# ------------------------------------------------------------- 3. 패턴과 Match
cat > "$work/match.conf" <<'CFG'
Match host "*.example.com"
    Port 2022
    IdentitiesOnly yes

Host short
    HostName 203.0.113.40

Match originalhost short
    Port 2200

Host !bastion *
    Port 2222
CFG

rule "3. 패턴, Match, 부정"
show_conf "$work/match.conf"
for target in app.example.com short bastion other; do
    printf -- '-- %s\n' "$target"
    resolve "$work/match.conf" "$target" hostname port identitiesonly
done

# --------------------------------------------------------------- 4. Include
cat > "$work/conf.d/extra.conf" <<'CFG'
Host cache
    HostName 203.0.113.30
    User redis
CFG

cat > "$work/include-rel.conf" <<'CFG'
Include probe_work/conf.d/*.conf

Host *
    Port 2222
CFG

cat > "$work/include-abs.conf" <<CFG
Include ${work_abs}/conf.d/*.conf

Host *
    Port 2222
CFG

rule "4. Include — 상대경로를 설정 파일 옆으로 보지 않는다"
show_conf "$work/include-rel.conf"
printf -- '-- ssh -G -F include-rel.conf cache\n'
resolve "$work/include-rel.conf" cache hostname port
printf -- '\n-- 같은 내용을 절대경로로 Include 하면\n'
resolve "$work/include-abs.conf" cache hostname port

# --------------------------------------------------- 5. 점프 호스트와 포워딩
cat > "$work/forward.conf" <<'CFG'
Host bastion
    HostName 203.0.113.9
    User jump
    Port 2200

Host db
    HostName 198.51.100.20
    User dbadmin
    ProxyJump bastion
    LocalForward 15432 127.0.0.1:5432
    RemoteForward 9000 127.0.0.1:9000
    DynamicForward 1080
    ExitOnForwardFailure yes
CFG

rule "5. 점프 호스트와 세 가지 포워딩이 풀린 모양"
show_conf "$work/forward.conf"
printf -- '-- ssh -G -F forward.conf db\n'
resolve "$work/forward.conf" db \
    user hostname port proxyjump localforward remoteforward dynamicforward exitonforwardfailure

# ------------------------------------------------- 6. 명령줄이 설정을 이긴다
rule "6. 명령줄 옵션과 설정 파일의 관계"
printf -- '-- -o User=override 를 붙이면\n'
ssh -T -G -F "$work/forward.conf" -o User=override db 2>&1 | grep -E '^user '
printf -- '\n-- -L 은 설정의 LocalForward 를 지우지 않고 더한다\n'
ssh -T -G -F "$work/forward.conf" -L 18080:127.0.0.1:8080 db 2>&1 | grep -E '^localforward '

rule "7. -G 가 찍는 전체 줄 수"
ssh -T -G -F "$work/forward.conf" db 2>&1 | wc -l

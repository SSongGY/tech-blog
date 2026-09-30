#!/usr/bin/env bash
# 환경변수와 셸 초기화 순서 — bash 를 띄우는 방식마다 어떤 파일을 읽는지 실측한다.
#
# 가짜 HOME(/tmp/shinit/home)에 초기화 파일을 깔고, 각 파일이 읽히면 한 줄씩 찍게 한다.
# 새 셸은 env -i 로 빈 환경에서 띄운다 — 지금 셸의 변수가 섞이면 무엇을 어디서 읽었는지 가려지기 때문이다.
# 시스템 파일은 고칠 수 없으므로 흔적으로 판별한다:
#   CONFIG_SITE  → Git Bash 의 /etc/profile 이 export 한다 (빈 환경이면 /etc/profile 을 읽었을 때만 있다)
#   PS1 이 값과 함께 export 됨 → /etc/bash.bashrc 가 대화형 셸에서 PS1 을 export 한다.
#                  로그인 셸은 /etc/profile 도 PS1 을 export 하므로 이 표식만으로 둘을 가를 수 없다
#                  (/etc/profile 이 /etc/bash.bashrc 를 직접 읽으므로 로그인·대화형이면 둘 다 읽힌 것이다).
# 터미널 없이 -i 로 띄우면 bash 가 "no job control" 경고 두 줄을 stderr 로 낸다. 셸마다 같은 줄이라 걸러 낸다.

set -u
BASE=/tmp/shinit
H="$BASE/home"
rm -rf "$BASE"
mkdir -p "$H" "$BASE/work"

section() { printf '\n== %s ==\n' "$1"; }
case_() { printf '\n[%s]\n  $ %s\n' "$1" "$2"; }

make_home() {
    rm -rf "$H"; mkdir -p "$H"
    for f in .bash_profile .bash_login .profile .bashrc .bash_logout .bash_env .alt_rc .posix_env; do
        printf 'echo "  [읽음] ~/%s"\n' "$f" > "$H/$f"
    done
}

# 새 셸 안에서 돌릴 확인 명령. 작은따옴표 안이라 새 셸에서 전개된다.
PROBE='echo "  [상태] login=$(shopt -q login_shell && echo 예 || echo 아니오) interactive=$([[ $- == *i* ]] && echo 예 || echo 아니오) /etc/profile=${CONFIG_SITE:+읽음} /etc/bash.bashrc=$(if shopt -q login_shell; then echo "(로그인 셸은 표식으로 못 가림)"; elif [[ $(declare -p PS1 2>/dev/null) == "declare -x PS1="* ]]; then echo 읽음; fi)"'

JOBCTL='terminal process group|no job control'
fresh() { env -i HOME="$H" PATH=/usr/bin:/bin TERM=dumb "$@" 2>&1 | grep -Ev "^$|$JOBCTL"; }

section "0. 버전"
bash --version | head -n 1
env --version | head -n 1

section "1. 띄우는 방식별로 읽는 파일"
make_home
case_ "1-A 비로그인·비대화형" "bash -c CMD"
fresh bash -c "$PROBE"
case_ "1-B 로그인·비대화형" "bash -l -c CMD"
fresh bash -l -c "$PROBE"
case_ "1-C 로그인·비대화형, 끝에 exit" "bash -l -c 'CMD; exit'"
fresh bash -l -c "$PROBE; exit"
case_ "1-D 비로그인·대화형" "bash -i -c CMD"
fresh bash -i -c "$PROBE"
case_ "1-E 로그인·대화형" "bash -l -i -c CMD"
fresh bash -l -i -c "$PROBE"
case_ "1-F 스크립트 파일 실행" "bash script.sh"
printf '%s\n' "$PROBE" > "$BASE/work/script.sh"
fresh bash "$BASE/work/script.sh"
case_ "1-G 스크립트 + BASH_ENV" "BASH_ENV=~/.bash_env bash script.sh"
env -i HOME="$H" PATH=/usr/bin:/bin BASH_ENV="$H/.bash_env" bash "$BASE/work/script.sh" 2>&1

section "2. 로그인 셸은 셋 중 처음 것 하나만 읽는다"
make_home
case_ "2-A 셋 다 있을 때" "bash -l -c CMD"
fresh bash -l -c "$PROBE"
rm "$H/.bash_profile"
case_ "2-B ~/.bash_profile 을 지우면" "bash -l -c CMD"
fresh bash -l -c "$PROBE"
rm "$H/.bash_login"
case_ "2-C ~/.bash_login 도 지우면" "bash -l -c CMD"
fresh bash -l -c "$PROBE"
case_ "2-D 흔한 해법 — .bash_profile 에서 .bashrc 를 읽는다" "bash -l -i -c CMD"
make_home
printf 'echo "  [읽음] ~/.bash_profile"\n[ -f ~/.bashrc ] && . ~/.bashrc\n' > "$H/.bash_profile"
fresh bash -l -i -c "$PROBE"

section "3. 초기화를 바꾸는 옵션"
make_home
case_ "3-A --noprofile" "bash --noprofile -l -c CMD"
fresh bash --noprofile -l -c "$PROBE"
case_ "3-B --norc" "bash --norc -i -c CMD"
fresh bash --norc -i -c "$PROBE"
case_ "3-C --rcfile 파일" "bash --rcfile ~/.alt_rc -i -c CMD"
fresh bash --rcfile "$H/.alt_rc" -i -c "$PROBE"
case_ "3-D --init-file 은 --rcfile 과 같다" "bash --init-file ~/.alt_rc -i -c CMD"
fresh bash --init-file "$H/.alt_rc" -i -c "$PROBE"
case_ "3-E --rcfile 을 로그인 셸에 주면" "bash --rcfile ~/.alt_rc -l -i -c CMD"
fresh bash --rcfile "$H/.alt_rc" -l -i -c "$PROBE"

section "4. sh 로 띄우면 (POSIX 흉내)"
make_home
case_ "4-A sh -l" "sh -l -c CMD"
fresh sh -l -c "$PROBE"
case_ "4-B sh -i — ~/.bashrc 대신 \$ENV" "ENV=~/.posix_env sh -i -c CMD"
fresh ENV="$H/.posix_env" sh -i -c "$PROBE"
case_ "4-C bash --posix -i 도 같다" "ENV=~/.posix_env bash --posix -i -c CMD"
fresh ENV="$H/.posix_env" bash --posix -i -c "$PROBE"

section "5. 셸 변수와 환경변수"
case_ "5-A export 하지 않은 변수는 자식에게 안 간다" "APP_MODE=dev; bash -c 'echo \${APP_MODE-없음}'"
APP_MODE=dev
bash -c 'echo "  자식: ${APP_MODE-없음}"'
export APP_MODE
bash -c 'echo "  export 뒤 자식: ${APP_MODE-없음}"'
case_ "5-B declare -p 로 속성 보기, export -n 으로 내보내기 끄기" "declare -p APP_MODE; export -n APP_MODE"
declare -p APP_MODE | sed 's/^/  /'
export -n APP_MODE
declare -p APP_MODE | sed 's/^/  /'
bash -c 'echo "  export -n 뒤 자식: ${APP_MODE-없음}"'
case_ "5-C 한 명령에만 주기" "APP_MODE=prod bash -c ...; echo \$APP_MODE"
APP_MODE=prod bash -c 'echo "  자식: $APP_MODE"'
echo "  부모: $APP_MODE"
case_ "5-D 자식이 바꾼 값은 부모로 돌아오지 않는다" "bash -c 'export CHILD_SET=1'"
bash -c 'export CHILD_SET=1'
echo "  부모의 CHILD_SET: ${CHILD_SET-없음}"
printf 'export CHILD_SET=sourced\n' > "$BASE/work/setvar.sh"
. "$BASE/work/setvar.sh"
echo "  source 뒤 CHILD_SET: ${CHILD_SET-없음}"
case_ "5-E set -a — 이후 대입을 전부 export" "set -a; AUTO_A=1; set +a; AUTO_B=2"
set -a; AUTO_A=1; set +a; AUTO_B=2
bash -c 'echo "  자식: AUTO_A=${AUTO_A-없음} AUTO_B=${AUTO_B-없음}"'
case_ "5-F 함수 내보내기" "export -f greet; bash -c greet"
greet() { echo "  함수 greet 실행"; }
bash -c 'greet' 2>&1 | sed 's/^/  /'
export -f greet
bash -c 'greet'
case_ "5-G export -p 는 declare -x 형식으로 찍는다" "export -p | grep APP_\|AUTO_"
export -p | grep -E ' (APP_MODE|AUTO_A|AUTO_B|CHILD_SET)=' | sed 's/^/  /'

section "6. env 와 printenv"
cd "$BASE/work"
export DEMO_A=1 DEMO_B=2
case_ "6-A 인자 없이 — 환경 목록" "env | grep ^DEMO_"
env | grep '^DEMO_' | sed 's/^/  /'
case_ "6-B -i — 빈 환경에서 시작. PATH 도 비므로 명령 이름만 주면" "env -i DEMO_C=3 env"
env -i DEMO_C=3 env 2>&1 | sed 's/^/  /'
echo "  종료 코드 ${PIPESTATUS[0]}"
case_ "6-C 절대경로로 주면" "env -i DEMO_C=3 /usr/bin/env"
env -i DEMO_C=3 /usr/bin/env | sed 's/^/  /'
case_ "6-D - 는 -i 와 같다" "env - DEMO_C=3 /usr/bin/env"
env - DEMO_C=3 /usr/bin/env | sed 's/^/  /'
case_ "6-E -u — 하나만 뺀다" "env -u DEMO_A env | grep ^DEMO_"
env -u DEMO_A env | grep '^DEMO_' | sed 's/^/  /'
case_ "6-F -C — 작업 폴더를 바꿔 실행" "env -C /tmp pwd"
env -C /tmp pwd | sed 's/^/  /'
case_ "6-G -0 — 줄 끝을 NUL 로 (값에 줄바꿈이 있어도 경계가 보인다)" "env -i 'MULTI=a<줄바꿈>b' X=1 /usr/bin/env [-0]"
echo "  -- -0 없이 (줄 수: 값의 줄바꿈과 경계가 섞인다)"
env -i "MULTI=a
b" X=1 /usr/bin/env | sed 's/^/  | /'
echo "  -- -0 으로, NUL 을 '|' 로 바꿔 찍음"
env -i "MULTI=a
b" X=1 /usr/bin/env -0 | tr '\0' '|' | sed 's/^/  /'; echo
case_ "6-H -S — 한 덩어리 문자열을 인자로 쪼갠다 (#! 줄용)" "env -S 'bash -c \"echo 두 인자\"'"
env -S 'bash -c "echo \"  쪼개진 뒤 실행: \$0\""'
printf '#!/usr/bin/env -S bash -e\necho "  -S 로 옵션을 붙인 #! 줄: $-"\n' > shebang_s.sh
chmod +x shebang_s.sh
./shebang_s.sh
printf '#!/usr/bin/env bash -e\necho "  -S 없이"\n' > shebang_plain.sh
chmod +x shebang_plain.sh
./shebang_plain.sh 2>&1 | sed 's/^/  /'
echo "  종료 코드 ${PIPESTATUS[0]}"
case_ "6-I -v — 처리 과정을 찍는다" "env -v -i DEMO_C=3 /usr/bin/true"
env -v -i DEMO_C=3 /usr/bin/true 2>&1 | sed 's/^/  /'
case_ "6-J 시그널 처리 — --ignore-signal / --list-signal-handling" "env --ignore-signal=INT --list-signal-handling true"
env --ignore-signal=INT --list-signal-handling true 2>&1 | sed 's/^/  /'
case_ "6-K printenv — 이름을 주면 값만, 없으면 종료 코드 1" "printenv DEMO_A NO_SUCH"
printenv DEMO_A NO_SUCH | sed 's/^/  /'
echo "  종료 코드 ${PIPESTATUS[0]}"
case_ "6-L 셸 변수는 printenv 에 안 보인다" "LOCAL_ONLY=1; printenv LOCAL_ONLY"
LOCAL_ONLY=1
printenv LOCAL_ONLY; echo "  종료 코드 $?"
echo "  셸에서는: $LOCAL_ONLY"

section "7. 초기화 파일에서 PATH 를 늘리면"
make_home
printf 'export PATH="$PATH:/opt/demo/bin"\n' > "$H/.bashrc"
case_ "7-A .bashrc 에 PATH 추가, 대화형 셸을 세 겹 띄우면" "bash -i -c 'bash -i -c \"bash -i -c ...\"'"
fresh bash -i -c 'bash -i -c "bash -i -c \"echo \\\"  PATH=\\\$PATH\\\"\""'
printf 'case ":$PATH:" in *:/opt/demo/bin:*) ;; *) export PATH="$PATH:/opt/demo/bin" ;; esac\n' > "$H/.bashrc"
case_ "7-B 이미 있으면 건너뛰게 고친 뒤" "같은 명령"
fresh bash -i -c 'bash -i -c "bash -i -c \"echo \\\"  PATH=\\\$PATH\\\"\""'
case_ "7-C PATH 가 아예 없는 빈 환경에서 bash 가 쓰는 PATH" "env -i /usr/bin/bash -c 'echo \$PATH'"
env -i /usr/bin/bash -c 'echo "  PATH=$PATH"; echo "  HOME=${HOME-없음}"; echo "  export 됐나: $(declare -p PATH)"'

cd /
rm -rf "$BASE"

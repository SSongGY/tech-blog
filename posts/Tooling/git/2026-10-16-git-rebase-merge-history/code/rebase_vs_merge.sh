#!/usr/bin/env bash
# 같은 작업을 merge 로 합쳤을 때와 rebase 로 올렸을 때를 나란히 만들어 비교한다.
#
# 저장소는 mktemp 로 만든 임시 폴더 안에만 생긴다. 이 글의 저장소를 건드리지
# 않고, 끝나면 남는 것도 없다. 커밋 날짜와 작성자를 고정해 두었으므로 몇 번을
# 돌려도 같은 해시가 나온다 — 글에 적은 해시와 실행 기록이 어긋나지 않는다.

set -eu

export GIT_AUTHOR_NAME='Example Author'
export GIT_AUTHOR_EMAIL='author@example.com'
export GIT_COMMITTER_NAME='Example Author'
export GIT_COMMITTER_EMAIL='author@example.com'

SANDBOX=$(mktemp -d)

rule() {
    printf '================================================================\n'
    printf '%s\n' "$1"
    printf '================================================================\n'
}

commit() {
    # $1 파일, $2 내용, $3 메시지, $4 날짜
    printf '%s\n' "$2" > "$1"
    git add "$1"
    GIT_AUTHOR_DATE="$4" GIT_COMMITTER_DATE="$4" git commit -q -m "$3"
}

rule "환경"
git --version
printf 'OS      %s\n' "$(uname -s)"
printf '\n'

# ---------------------------------------------------------------- 출발점
cd "$SANDBOX"
git init -q -b main base
cd base
git config user.name 'Example Author'
git config user.email 'author@example.com'
git config core.autocrlf false   # 윈도우에서 줄바꿈 경고가 섞이지 않게

commit app.txt 'v1'            'feat: 초기 버전'            '2026-01-01T09:00:00+09:00'
commit app.txt 'v2'            'feat: 조회 기능'            '2026-01-02T09:00:00+09:00'
git switch -q -c feature
commit lib.txt 'ok'            'feat: 공통 모듈'            '2026-01-03T09:00:00+09:00'
commit lib.txt 'broken'        'refactor: 공통 모듈 정리'   '2026-01-04T09:00:00+09:00'
git switch -q main
commit docs.txt 'readme'       'docs: 사용법'               '2026-01-05T09:00:00+09:00'
commit docs.txt 'readme+faq'   'docs: 자주 묻는 질문'       '2026-01-06T09:00:00+09:00'

rule "공통 출발점 — feature 가 main 에서 갈라진 뒤 양쪽이 각각 나아갔다"
git log --graph --oneline --all --date-order
printf '\n'
printf 'feature 가 갈라져 나온 지점: %s\n\n' "$(git merge-base main feature | cut -c1-7)"

# ---------------------------------------------------------------- ① merge
cd "$SANDBOX"
git clone -q -c core.autocrlf=false base merged
cd merged
git config user.name 'Example Author'
git config user.email 'author@example.com'
git switch -q -c feature origin/feature
git switch -q main

rule "① git merge --no-ff feature"
GIT_AUTHOR_DATE='2026-01-07T09:00:00+09:00' \
GIT_COMMITTER_DATE='2026-01-07T09:00:00+09:00' \
    git merge -q --no-ff -m 'merge: 공통 모듈 반영' feature
git log --graph --oneline
printf '\n'
printf '전체 커밋 수            : %s\n' "$(git rev-list --count HEAD)"
printf '머지 커밋 수            : %s\n' "$(git rev-list --count --merges HEAD)"
printf 'first-parent 만 따라가면: %s 개\n\n' "$(git rev-list --count --first-parent HEAD)"

printf -- '-- git log --oneline --first-parent (주 줄기만)\n'
git log --oneline --first-parent
printf '\n'

# ---------------------------------------------------------------- ② rebase
cd "$SANDBOX"
git clone -q -c core.autocrlf=false base rebased
cd rebased
git config user.name 'Example Author'
git config user.email 'author@example.com'
git switch -q -c feature origin/feature

rule "② git rebase main 뒤 fast-forward 로 합쳤을 때"
printf -- '-- rebase 전 feature 의 커밋\n'
git log --oneline -2 --format='%h %ad %cd %s' --date=format:'%Y-%m-%d'
printf '\n'

GIT_COMMITTER_DATE='2026-01-07T09:00:00+09:00' git rebase -q main

printf -- '-- rebase 후 같은 커밋 (작성일은 그대로, 커밋일과 해시가 바뀐다)\n'
git log --oneline -2 --format='%h %ad %cd %s' --date=format:'%Y-%m-%d'
printf '\n'

git switch -q main
git merge -q --ff-only feature
git log --graph --oneline
printf '\n'
printf '전체 커밋 수            : %s\n' "$(git rev-list --count HEAD)"
printf '머지 커밋 수            : %s\n' "$(git rev-list --count --merges HEAD)"
printf '\n'

# ------------------------------------------------- ③ 결과물이 같은지 확인
rule "③ 두 방식의 최종 작업 트리가 같은지 — 트리 해시를 비교한다"
MERGED_TREE=$(git -C "$SANDBOX/merged" rev-parse 'HEAD^{tree}')
REBASED_TREE=$(git -C "$SANDBOX/rebased" rev-parse 'HEAD^{tree}')
printf 'merge  쪽 트리 : %s\n' "$MERGED_TREE"
printf 'rebase 쪽 트리 : %s\n' "$REBASED_TREE"
if [ "$MERGED_TREE" = "$REBASED_TREE" ]; then
    printf '판정           : 같다 — 파일 내용은 똑같고 히스토리 모양만 다르다\n\n'
else
    printf '판정           : 다르다\n\n'
fi

# ------------------------------------------------------------- ④ bisect
rule "④ git bisect 가 'broken' 이 들어온 커밋을 찾는 데 몇 번 걸리는가"
cat > "$SANDBOX/check.sh" <<'CHECK'
#!/usr/bin/env bash
# lib.txt 가 없으면 아직 그 기능이 안 들어온 시점이므로 정상으로 본다
[ -f lib.txt ] || exit 0
grep -q broken lib.txt && exit 1
exit 0
CHECK
chmod +x "$SANDBOX/check.sh"

for repo in merged rebased; do
    printf -- '-- %s 쪽\n' "$repo"
    cd "$SANDBOX/$repo"
    git bisect start HEAD "$(git rev-list --max-parents=0 HEAD)" 2>&1 | sed 's/^/   /'
    git bisect run "$SANDBOX/check.sh" 2>&1 \
        | grep -E 'revisions left|is the first bad commit|refactor' \
        | sed 's/^/   /'
    git bisect reset -q 2>/dev/null || git bisect reset > /dev/null
    printf '\n'
done

rule "⑤ merge 쪽에서 --first-parent 를 붙이면 분기 안으로 들어가지 않는다"
cd "$SANDBOX/merged"
git bisect start --first-parent HEAD "$(git rev-list --max-parents=0 HEAD)" 2>&1 | sed 's/^/   /'
git bisect run "$SANDBOX/check.sh" 2>&1 \
    | grep -E 'revisions left|is the first bad commit|merge:|refactor' \
    | sed 's/^/   /'
git bisect reset -q 2>/dev/null || git bisect reset > /dev/null
printf '\n'
printf '   rebase 쪽에는 머지 커밋이 없으므로 --first-parent 가 아무것도 줄이지 못한다.\n'

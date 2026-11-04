#!/usr/bin/env bash
# 커밋 하나를 만들고 .git/objects 안의 blob·tree·commit 을 차례로 열어 본다.
#
# 저장소는 mktemp 로 만든 임시 폴더 안에만 생긴다. 이 글의 저장소를 건드리지
# 않고, 끝나면 남는 것도 없다. 작성자와 날짜를 고정했으므로 몇 번을 돌려도
# 같은 해시가 나온다 — 글에 적은 해시와 실행 기록이 어긋나지 않는다.

set -eu

export GIT_AUTHOR_NAME='Example Author'
export GIT_AUTHOR_EMAIL='author@example.com'
export GIT_COMMITTER_NAME='Example Author'
export GIT_COMMITTER_EMAIL='author@example.com'

SANDBOX=$(mktemp -d)

rule() {
    printf '\n================================================================\n'
    printf '%s\n' "$1"
    printf '================================================================\n'
}

objects() {
    # .git/objects 아래 낱개(loose) 객체를 "종류 해시 크기" 로 나열한다
    find .git/objects -type f -path '*/[0-9a-f][0-9a-f]/*' \
        | sed 's|.git/objects/||; s|/||' \
        | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize)' \
        | sort
}

commit_at() {
    # $1 메시지, $2 날짜
    GIT_AUTHOR_DATE="$2" GIT_COMMITTER_DATE="$2" git commit -q -m "$1"
}

rule "환경"
git --version
sha1sum --version | head -1

cd "$SANDBOX"
git init -q -b main repo
cd repo
git config core.autocrlf false   # 윈도우에서 줄바꿈이 바뀌면 해시가 달라진다

# ---------------------------------------------------------------- ① blob
rule "① 파일 하나를 add 만 했을 때 — blob 하나가 생긴다"
printf 'hello\n' > a.txt
git add a.txt
objects
printf '\n'
BLOB=$(git hash-object a.txt)
printf -- '-- git cat-file -t / -s / -p %s\n' "$BLOB"
git cat-file -t "$BLOB"
git cat-file -s "$BLOB"
git cat-file -p "$BLOB"
printf '\n'
printf -- '-- 해시를 손으로 계산한다: sha1("blob 6\\0" + 내용)\n'
printf 'blob 6\0hello\n' | sha1sum
printf -- '-- 저장된 파일 경로 (앞 2자리가 폴더)\n'
find .git/objects -type f -path '*/[0-9a-f][0-9a-f]/*' | sed 's|.git/objects/||'
printf -- '-- 디스크 위 크기 (zlib 압축된 "blob 6\\0hello\\n")\n'
wc -c < ".git/objects/${BLOB:0:2}/${BLOB:2}"

# ---------------------------------------------------------------- ② tree, commit
rule "② 커밋하면 tree 와 commit 이 더해진다 — 객체 3개"
commit_at 'feat: a.txt 추가' '2026-01-01T09:00:00+09:00'
objects
printf '\n'
printf -- '-- git cat-file -p HEAD (commit)\n'
git cat-file -p HEAD
printf '\n'
printf -- '-- git cat-file -p HEAD^{tree} (tree)\n'
git cat-file -p 'HEAD^{tree}'

# ---------------------------------------------------------------- ③ 같은 내용 복사
rule "③ 같은 내용의 파일을 복사해 커밋하면 — blob 은 늘지 않는다"
cp a.txt b.txt
git add b.txt
commit_at 'feat: a.txt 를 b.txt 로 복사' '2026-01-02T09:00:00+09:00'
objects
printf '\n'
printf -- '-- tree 를 열면 두 항목이 같은 blob 을 가리킨다\n'
git cat-file -p 'HEAD^{tree}'

# ---------------------------------------------------------------- ④ 이름 변경
rule "④ 파일 이름만 바꿔 커밋하면 — tree 와 commit 만 새로 생긴다"
git mv b.txt c.txt
commit_at 'refactor: b.txt 를 c.txt 로' '2026-01-03T09:00:00+09:00'
objects
printf '\n'
printf -- '-- 두 커밋의 tree 는 다르지만 blob 은 같다\n'
printf 'HEAD~1 tree : %s\n' "$(git rev-parse 'HEAD~1^{tree}')"
printf 'HEAD   tree : %s\n' "$(git rev-parse 'HEAD^{tree}')"
git cat-file -p 'HEAD^{tree}'
printf '\n'
printf -- '-- git 은 이름 변경을 저장하지 않고, 보여 줄 때 blob 이 같은 것을 보고 추정한다\n'
git show --stat --format='%h %s' HEAD | sed '/^$/d'

# ---------------------------------------------------------------- ⑤ 내용 변경
rule "⑤ 한 글자만 바꿔도 — blob 은 통째로 새로 생긴다 (낱개 객체는 차분 저장이 없다)"
printf 'hello!\n' > a.txt
git add a.txt
commit_at 'fix: 느낌표' '2026-01-04T09:00:00+09:00'
objects
printf '\n'
git cat-file -p 'HEAD^{tree}'

# ---------------------------------------------------------------- ⑥ 디렉터리
rule "⑥ 폴더를 넣으면 — tree 가 tree 를 가리킨다"
mkdir docs
printf 'readme\n' > docs/README.md
git add docs
commit_at 'docs: README 추가' '2026-01-05T09:00:00+09:00'
printf -- '-- 최상위 tree\n'
git cat-file -p 'HEAD^{tree}'
printf '\n'
printf -- '-- docs tree\n'
git cat-file -p 'HEAD:docs'
printf '\n'
printf '낱개 객체 수 : %s\n' "$(git count-objects -v | sed -n 's/^count: //p')"
printf 'blob %s · tree %s · commit %s\n' \
    "$(objects | grep -c '^blob')" \
    "$(objects | grep -c '^tree')" \
    "$(objects | grep -c '^commit')"

# ---------------------------------------------------------------- ⑦ pack
rule "⑦ git gc 뒤 — 낱개 객체가 pack 하나로 묶이고 그제야 차분이 쓰인다"
git gc -q
git count-objects -v | grep -E '^(count|in-pack|packs):'
printf '\n'
printf -- '-- git verify-pack -v : 종류 크기 pack안크기 [깊이 기준객체]\n'
git verify-pack -v .git/objects/pack/*.idx \
    | grep -E '^[0-9a-f]{40} (blob|tree|commit)' \
    | sort -k2,2 -k3,3n

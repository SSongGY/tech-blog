# merge 와 rebase 비교 예제

같은 분기 작업을 `git merge --no-ff` 로 합친 저장소와 `git rebase` 로 올린 저장소를
각각 만들어, 그래프 모양·커밋 수·해시·`git bisect` 결과를 나란히 비교한다.

저장소는 `mktemp -d` 가 만든 임시 폴더 안에만 생긴다. 이 저장소를 건드리지 않고,
끝나면 남는 것도 없다. 작성자와 커밋 날짜를 고정했으므로 몇 번을 돌려도 같은
해시가 나온다.

## 실행

```bash
bash rebase_vs_merge.sh
```

## 바꿔 볼 값

- `git merge --no-ff` 에서 `--no-ff` 를 빼면 어떻게 되는지 본다.
  이 예제는 main 쪽에도 커밋이 있어 fast-forward 가 안 되므로 결과가 같다.
  `docs:` 커밋 둘을 지우면 그때는 `--no-ff` 유무가 갈린다
- `git rebase -q main` 을 `git rebase -q --onto main feature~2 feature` 로 바꾸면
  올릴 커밋 범위를 직접 고르게 된다
- ④의 `check.sh` 가 보는 파일을 `app.txt` 로 바꾸면 분기 밖 커밋이 범인이 되고,
  그때 `bisect` 가 훑는 커밋 수가 어떻게 달라지는지 본다

## 파일

| 파일 | 무엇 |
|---|---|
| `rebase_vs_merge.sh` | 예제 본문 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록. 손으로 고치지 않는다 |

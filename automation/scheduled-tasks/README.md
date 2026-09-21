# 스케줄 작업 정의

이 폴더의 `.md` 네 개는 **Claude Code 스케줄 작업의 원본**이다. 실제 작업은
`~/.claude/scheduled-tasks/<taskId>/SKILL.md`에 저장되는데, 그 폴더는 머신에 묶여 있어
저장소에 들어오지 않는다. 그래서 여기에 사본을 둔다.

| 파일 | taskId | cron | 하는 일 |
|---|---|---|---|
| `tech-blog-daily.md` | `tech-blog-daily` | `0 7,21 * * *` | 회차당 3편 |
| `tech-blog-exam.md` | `tech-blog-exam` | `0 15 * * *` | 기출 답안 (단답형 2 / 논술형 1) |
| `tech-blog-concept.md` | `tech-blog-concept` | `0 17 * * *` | 15시 답안에서 나온 개념을 `pe` 글 2편으로 |
| `tech-blog-healthcheck.md` | `tech-blog-healthcheck` | `0 9 * * *` | 점검만. 저장소 수정 금지 |

cron은 **UTC가 아니라 로컬 시각**으로 해석된다.

## 새 PC에 등록하기

Claude Code에 이렇게 말하면 된다. 네 개를 한 번에 시켜도 되고 하나씩 해도 된다.

> `automation/scheduled-tasks/tech-blog-exam.md`를 읽고, 그 내용을 프롬프트로 해서
> `tech-blog-exam` 스케줄 작업을 `0 15 * * *`로 만들어줘.

작업 프롬프트 안에 `D:\workspace\claude\tech_blog` 같은 **절대경로가 들어 있으니
새 PC의 경로로 바꿔서** 등록한다.

## 어긋났는지 확인

```bash
PYTHONUTF8=1 python scripts/blog.py tasks-diff
```

각 작업을 실제 작업과 하나씩 대조해 `[같음]` / `[다름]` / `[없음]` / `[사본없음]`을 낸다.
줄 끝 차이(CRLF vs LF)는 어긋난 것으로 보지 않는다. 어긋나면 종료 코드가 1이다.

**매일 9시 점검 루틴이 이 명령을 돌린다.** 어긋나면 보고만 하고 고치지는 않는다 —
어느 쪽이 맞는지는 사람이 정한다.

실제 작업 폴더가 다른 곳이면 `SCHEDULED_TASKS_DIR` 환경변수로 지정한다.

**이 대조는 파일만 본다.** 작업을 앱에서 지워도 `SKILL.md` 폴더는 남을 수 있고,
그때는 `[같음]`으로 넘어간다. 등록 자체가 맞는지는 `list_scheduled_tasks` 결과와
이 폴더의 목록을 견줘야 알 수 있다. 점검 루틴이 그 대조를 한다.

## 고칠 때

**`~/.claude/scheduled-tasks/` 쪽만 고치고 끝내지 않는다.** 그러면 이 사본이 낡는다.
둘 중 하나로 한다.

- 실제 작업을 고쳤으면 → 이 폴더로 다시 복사해 커밋
- 이 파일을 고쳤으면 → 실제 작업 프롬프트에도 반영

```bash
# 실제 작업 -> 저장소 (윈도우 기준 경로)
for t in daily exam concept healthcheck; do
  cp "$HOME/.claude/scheduled-tasks/tech-blog-$t/SKILL.md" \
     "automation/scheduled-tasks/tech-blog-$t.md"
done
```

## 주의

**네 작업이 같은 저장소에 쓴다.** 그래서 각 프롬프트에 "다른 회차가 `running`이면
저장소를 건드리지 않는다"가 들어 있다. 시각을 바꿀 때 회차가 겹치지 않게 간격을 둔다.
3편 쓰는 데 30분 안팎, 기출 답안은 30분 안팎 걸린다.

**앱이 켜져 있어야 돈다.** 앱이 꺼져 있던 시각의 회차는 다음 실행 때 밀려서 돈다.

"""캐시 쓰기 정책 6가지(적중 2 x 쓸모 있는 미스 조합)를 직접 사상 캐시로 돌려 하위 트래픽을 센다.

모델 (Jouppi, DEC WRL 91/12 §4 의 정의를 따른다)
- 직접 사상, 줄 LINE_WORDS 워드, 줄 LINE_COUNT 개. 주소는 워드 단위
- 줄마다 워드별 유효 비트. write-validate 만 일부 워드가 무효인 줄을 만든다
- 읽기 미스 = 하위에서 줄을 읽어 오는 일 1회(이미 유효한 워드는 덮지 않는다)
- WT: 쓰기마다 그 워드를 하위로 보낸다 (쓰기 버퍼는 두지 않는다)
- WB: 고친 줄을 교체할 때 유효한 워드를 하위로 보낸다. 끝에 남은 dirty 줄은 따로 센다
"""
LINE_WORDS = 4
LINE_COUNT = 8

POLICIES = [
    ("WT", "fetch-on-write"),
    ("WT", "write-validate"),
    ("WT", "write-around"),
    ("WT", "write-invalidate"),
    ("WB", "fetch-on-write"),
    ("WB", "write-validate"),
]


class Cache:
    def __init__(self, hit_policy, miss_policy):
        self.hit_policy = hit_policy
        self.miss_policy = miss_policy
        self.tags = [None] * LINE_COUNT
        self.valid = [[False] * LINE_WORDS for _ in range(LINE_COUNT)]
        self.dirty = [False] * LINE_COUNT
        self.line_fetches = 0
        self.words_fetched = 0
        self.words_written = 0

    def _locate(self, address):
        line_number, offset = divmod(address, LINE_WORDS)
        return line_number % LINE_COUNT, line_number, offset

    def _evict(self, index):
        if self.dirty[index]:
            self.words_written += sum(self.valid[index])
        self.dirty[index] = False
        self.valid[index] = [False] * LINE_WORDS

    def _claim(self, index, tag):
        if self.tags[index] != tag:
            self._evict(index)
            self.tags[index] = tag

    def _fetch(self, index):
        self.line_fetches += 1
        self.words_fetched += self.valid[index].count(False)
        self.valid[index] = [True] * LINE_WORDS

    def read(self, address):
        index, tag, offset = self._locate(address)
        if self.tags[index] == tag and self.valid[index][offset]:
            return
        self._claim(index, tag)
        self._fetch(index)

    def write(self, address):
        index, tag, offset = self._locate(address)
        hit = self.tags[index] == tag and self.valid[index][offset]
        if not hit:
            if self.miss_policy == "fetch-on-write":
                self._claim(index, tag)
                self._fetch(index)
            elif self.miss_policy == "write-validate":
                self._claim(index, tag)
                self.valid[index][offset] = True
            elif self.miss_policy == "write-invalidate":
                # 태그 확인과 동시에 데이터를 써 버렸으므로 그 줄은 버린다
                self._evict(index)
                self.tags[index] = None
            # write-around: 캐시 줄은 그대로 두고 하위로만 쓴다
        cached = hit or self.miss_policy in ("fetch-on-write", "write-validate")
        if self.hit_policy == "WT" or not cached:
            self.words_written += 1
        else:
            self.dirty[index] = True

    def dirty_words_left(self):
        return sum(sum(v) for v, d in zip(self.valid, self.dirty) if d)


def pattern_copy():
    """블록 복사: 원본을 읽고 목적지에 쓴다. 목적지 옛 내용은 읽지 않는다."""
    ops = []
    for i in range(32):
        ops += [("R", i), ("W", 72 + i)]
    return ops


def pattern_produce_consume():
    """버퍼를 채우고 곧바로 다시 읽는다."""
    return [("W", 200 + i) for i in range(16)] + [("R", 200 + i) for i in range(16)]


def pattern_read_modify_write():
    """saxpy 처럼 읽은 자리에 다시 쓴다."""
    ops = []
    for i in range(32):
        ops += [("R", 400 + i), ("W", 400 + i)]
    return ops


def pattern_write_then_reread_inputs():
    """입력을 읽고, 같은 줄로 사상되는 곳에 결과를 쓰고, 입력을 다시 읽는다."""
    inputs = [("R", i) for i in range(16)]
    results = [("W", LINE_WORDS * LINE_COUNT + i) for i in range(16)]
    return inputs + results + inputs


def pattern_repeated_counter_updates():
    """카운터 4개를 16번씩 고친다. 같은 워드에 쓰기가 반복된다."""
    ops = []
    for _ in range(16):
        for i in range(4):
            ops += [("R", 600 + i), ("W", 600 + i)]
    return ops


PATTERNS = [
    ("① 블록 복사", pattern_copy),
    ("② 쓰고 바로 다시 읽기", pattern_produce_consume),
    ("③ 읽고-고치고-쓰기", pattern_read_modify_write),
    ("④ 결과를 쓰고 입력을 다시 읽기", pattern_write_then_reread_inputs),
    ("⑤ 같은 카운터를 반복해 고치기", pattern_repeated_counter_updates),
]


def run(ops, hit_policy, miss_policy):
    cache = Cache(hit_policy, miss_policy)
    for kind, address in ops:
        if kind == "R":
            cache.read(address)
        else:
            cache.write(address)
    return cache


def main():
    print(f"캐시: 직접 사상, 줄 {LINE_COUNT}개 x {LINE_WORDS}워드 = {LINE_COUNT * LINE_WORDS}워드")
    print()
    for title, make in PATTERNS:
        ops = make()
        reads = sum(kind == "R" for kind, _ in ops)
        print(f"== {title}: 읽기 {reads} · 쓰기 {len(ops) - reads} ==")
        print("  적중 | 미스 정책         | 줄 읽기 | 읽은 워드 | 내린 워드 | 끝에 남은 dirty | 합계")
        fetches = {}
        for hit_policy, miss_policy in POLICIES:
            cache = run(ops, hit_policy, miss_policy)
            left = cache.dirty_words_left()
            total = cache.words_fetched + cache.words_written + left
            fetches[(hit_policy, miss_policy)] = cache.line_fetches
            print(f"  {hit_policy}   | {miss_policy:17} | {cache.line_fetches:7} |"
                  f" {cache.words_fetched:9} | {cache.words_written:9} | {left:15} | {total:4}")
        wt = {miss: fetches[("WT", miss)] for _, miss in POLICIES[:4]}
        ordered = (wt["fetch-on-write"] >= wt["write-invalidate"]
                   >= max(wt["write-around"], wt["write-validate"]))
        print(f"  Jouppi Figure 17 순서(FoW >= invalidate >= around, validate) 성립: {ordered}")
        print()


if __name__ == "__main__":
    main()

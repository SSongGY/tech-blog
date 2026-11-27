"""Bitcask 논문(Sheehy·Smith, 2010)의 구조를 파이썬으로 옮긴 최소 구현.

데이터 항목 형식은 basho/bitcask 소스(bitcask_fileops.erl, bitcask.hrl)를 따른다.
  데이터 파일 항목 : crc32(4) | tstamp(4) | key_sz(2) | value_sz(4) | key | value
                     CRC 는 tstamp 부터 value 끝까지를 덮는다
  힌트 파일 항목   : tstamp(4) | key_sz(2) | total_sz(4) | tomb(1비트)+offset(63비트) | key
"""
import os
import struct
import zlib

DATA_HEADER = struct.Struct(">IIHI")  # crc, tstamp, key_sz, value_sz — 14바이트
HINT_HEADER = struct.Struct(">IHIQ")  # tstamp, key_sz, total_sz, tomb+offset — 18바이트
TOMBSTONE = b"bitcask_tombstone"
TOMB_BIT = 1 << 63


class KeydirEntry:
    """keydir 한 칸 — 값이 어느 파일 어느 위치에 몇 바이트로 있는가."""

    __slots__ = ("file_id", "value_sz", "value_pos", "tstamp")

    def __init__(self, file_id, value_sz, value_pos, tstamp):
        self.file_id = file_id
        self.value_sz = value_sz
        self.value_pos = value_pos
        self.tstamp = tstamp


class Bitcask:
    def __init__(self, directory, max_file_size=64 * 1024):
        self.directory = directory
        self.max_file_size = max_file_size
        self.keydir = {}
        self.clock = 0          # 결과를 매번 같게 하려고 실제 시각 대신 증가하는 수를 쓴다
        self.read_calls = 0     # get 이 파일을 몇 번 읽었는가
        self.startup_bytes = 0  # 기동할 때 keydir 를 만들려고 읽은 바이트
        os.makedirs(directory, exist_ok=True)
        self._load_keydir()
        self.active_id = max(self._file_ids(), default=0) + 1
        self.active = open(self._data_path(self.active_id), "ab")

    # ---- 파일 이름 ----
    def _data_path(self, file_id):
        return os.path.join(self.directory, f"{file_id:06d}.data")

    def _hint_path(self, file_id):
        return os.path.join(self.directory, f"{file_id:06d}.hint")

    def _file_ids(self):
        return sorted(int(name[:6]) for name in os.listdir(self.directory)
                      if name.endswith(".data"))

    # ---- 쓰기 ----
    def _append(self, key, value):
        self.clock += 1
        body = struct.pack(">IHI", self.clock, len(key), len(value)) + key + value
        record = struct.pack(">I", zlib.crc32(body)) + body
        if self.active.tell() + len(record) > self.max_file_size:
            self._rotate()
        offset = self.active.tell()
        self.active.write(record)
        self.active.flush()
        value_pos = offset + DATA_HEADER.size + len(key)
        return KeydirEntry(self.active_id, len(value), value_pos, self.clock)

    def _rotate(self):
        # 크기 한도에 닿은 활성 파일은 닫히고 다시는 쓰이지 않는다
        self.active.close()
        self.active_id += 1
        self.active = open(self._data_path(self.active_id), "ab")

    def put(self, key, value):
        self.keydir[key] = self._append(key, value)

    def delete(self, key):
        self._append(key, TOMBSTONE)
        self.keydir.pop(key, None)

    # ---- 읽기 ----
    def get(self, key):
        entry = self.keydir.get(key)
        if entry is None:
            return None
        with open(self._data_path(entry.file_id), "rb") as f:
            f.seek(entry.value_pos)
            self.read_calls += 1
            return f.read(entry.value_sz)

    # ---- 기동: keydir 다시 만들기 ----
    def _load_keydir(self):
        for file_id in self._file_ids():
            if os.path.exists(self._hint_path(file_id)):
                self._load_from_hint(file_id)
            else:
                self._load_from_data(file_id)

    def _load_from_data(self, file_id):
        with open(self._data_path(file_id), "rb") as f:
            data = f.read()
        self.startup_bytes += len(data)
        offset = 0
        while offset + DATA_HEADER.size <= len(data):
            crc, tstamp, key_sz, value_sz = DATA_HEADER.unpack_from(data, offset)
            end = offset + DATA_HEADER.size + key_sz + value_sz
            if end > len(data) or zlib.crc32(data[offset + 4:end]) != crc:
                print(f"    파일 {file_id} 오프셋 {offset}: CRC 불일치 또는 잘린 항목 — 여기서 읽기를 멈춘다")
                break
            key_start = offset + DATA_HEADER.size
            key = data[key_start:key_start + key_sz]
            value_pos = key_start + key_sz
            if data[value_pos:end] == TOMBSTONE:
                self.keydir.pop(key, None)
            else:
                self.keydir[key] = KeydirEntry(file_id, value_sz, value_pos, tstamp)
            self.clock = max(self.clock, tstamp)
            offset = end

    def _load_from_hint(self, file_id):
        with open(self._hint_path(file_id), "rb") as f:
            data = f.read()
        self.startup_bytes += len(data)
        offset = 0
        while offset < len(data):
            tstamp, key_sz, total_sz, packed = HINT_HEADER.unpack_from(data, offset)
            key_start = offset + HINT_HEADER.size
            key = data[key_start:key_start + key_sz]
            record_offset = packed & ~TOMB_BIT
            value_sz = total_sz - DATA_HEADER.size - key_sz
            value_pos = record_offset + DATA_HEADER.size + key_sz
            self.keydir[key] = KeydirEntry(file_id, value_sz, value_pos, tstamp)
            self.clock = max(self.clock, tstamp)
            offset = key_start + key_sz

    # ---- 병합 ----
    def merge(self):
        """닫힌(불변) 파일만 훑어 살아 있는 최신 값만 새 파일에 다시 쓰고 힌트 파일을 만든다."""
        old_ids = [i for i in self._file_ids() if i != self.active_id]
        if not old_ids:
            return
        live = [(k, e) for k, e in self.keydir.items() if e.file_id in old_ids]
        # 결과 파일은 닫힌 파일 중 가장 큰 번호를 물려받는다. 활성 파일보다 번호가 작아야
        # 다음 기동 때 번호 순으로 읽어도 활성 파일의 새 값이 병합 결과를 덮는다
        merged_id = max(old_ids)
        tmp_data = os.path.join(self.directory, "merge.tmp")
        tmp_hint = os.path.join(self.directory, "merge-hint.tmp")
        new_entries = {}

        with open(tmp_data, "wb") as data_file, open(tmp_hint, "wb") as hint_file:
            for key, entry in sorted(live, key=lambda item: item[1].tstamp):
                with open(self._data_path(entry.file_id), "rb") as src:
                    src.seek(entry.value_pos)
                    value = src.read(entry.value_sz)
                body = struct.pack(">IHI", entry.tstamp, len(key), len(value)) + key + value
                record = struct.pack(">I", zlib.crc32(body)) + body
                offset = data_file.tell()
                data_file.write(record)
                hint_file.write(HINT_HEADER.pack(entry.tstamp, len(key), len(record), offset) + key)
                new_entries[key] = KeydirEntry(
                    merged_id, len(value), offset + DATA_HEADER.size + len(key), entry.tstamp)
        for file_id in old_ids:
            os.remove(self._data_path(file_id))
            if os.path.exists(self._hint_path(file_id)):
                os.remove(self._hint_path(file_id))
        os.replace(tmp_data, self._data_path(merged_id))
        os.replace(tmp_hint, self._hint_path(merged_id))
        self.keydir.update(new_entries)

    def close(self):
        self.active.close()

    # ---- 측정용 ----
    def disk_usage(self):
        total = 0
        for name in os.listdir(self.directory):
            total += os.path.getsize(os.path.join(self.directory, name))
        return total

    def file_summary(self):
        names = sorted(os.listdir(self.directory))
        data = [n for n in names if n.endswith(".data")]
        hint = [n for n in names if n.endswith(".hint")]
        return len(data), len(hint)

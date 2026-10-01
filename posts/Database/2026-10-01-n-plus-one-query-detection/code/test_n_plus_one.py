"""글 목록 화면에 N+1 이 들어오면 실패하는 테스트.

데이터를 일부러 저자 20명으로 만든다. 저자가 1~2명이면 지연 로딩도
문장이 2~3개라 탐지기의 허용치(같은 모양 2회) 안에 들어가 버린다.
"""

import unittest

from n_plus_one import (
    assert_no_repeated_query,
    build_database,
    render_in_batch,
    render_join,
    render_lazy,
)


class PostListQueryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = build_database(author_count=20)

    def tearDown(self) -> None:
        self.conn.close()

    def test_lazy_loading(self) -> None:
        with assert_no_repeated_query(self.conn):
            render_lazy(self.conn)

    def test_join(self) -> None:
        with assert_no_repeated_query(self.conn):
            render_join(self.conn)

    def test_in_batch(self) -> None:
        with assert_no_repeated_query(self.conn):
            render_in_batch(self.conn)


if __name__ == "__main__":
    unittest.main(verbosity=2)

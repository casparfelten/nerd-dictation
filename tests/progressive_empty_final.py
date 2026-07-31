#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

"""Regression tests for progressive output when Vosk withdraws a partial."""

import importlib.machinery
import os
import unittest
from typing import List, Tuple


nerd_dictation = importlib.machinery.SourceFileLoader(
    "nerd_dictation",
    os.path.join(os.path.dirname(__file__), "..", "nerd-dictation"),
).load_module()


class ProgressiveSession:
    def __init__(self) -> None:
        self.finalized: List[str] = []
        self.current = ""
        self.processed: List[str] = []
        self.output: List[Tuple[int, str]] = []

    def recognize(self, text: str, *, partial: bool) -> None:
        def process(value: str) -> str:
            self.processed.append(value)
            return value

        self.current = nerd_dictation.handle_progressive_text(
            text,
            partial,
            progressive_continuous=False,
            text_list=self.finalized,
            text_prev=self.current,
            process_fn=process,
            handle_fn=lambda delete, insert: self.output.append((delete, insert)),
        )


class TestProgressiveEmptyFinal(unittest.TestCase):
    def test_empty_final_retracts_first_partial(self) -> None:
        session = ProgressiveSession()
        session.recognize("discard me", partial=True)
        session.recognize("", partial=False)

        self.assertEqual(session.processed, ["discard me", ""])
        self.assertEqual(session.output, [(0, "discard me"), (10, "")])
        self.assertEqual(session.current, "")
        self.assertEqual(session.finalized, [])

        session.recognize("later", partial=False)
        self.assertEqual(session.processed[-1], "later")

    def test_empty_final_preserves_finalized_prefix(self) -> None:
        session = ProgressiveSession()
        session.recognize("keep", partial=False)
        session.recognize("discard me", partial=True)
        session.recognize("", partial=False)

        self.assertEqual(session.processed[-1], "keep")
        self.assertEqual(session.output[-1], (11, ""))
        self.assertEqual(session.current, "keep")
        self.assertEqual(session.finalized, ["keep"])

        session.recognize("later", partial=False)
        self.assertEqual(session.processed[-1], "keep later")
        self.assertEqual(session.finalized, ["keep", "later"])


if __name__ == "__main__":
    unittest.main()

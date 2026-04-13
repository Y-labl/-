"""OCR 解析与空任务栏检测（纯文本，不加载 Paddle、不截图）。"""
from __future__ import annotations

import unittest

from bot.models import GhostTaskInfo
from bot.ocr_task import is_empty_task_tracker, parse_task_text


class TestEmptyTracker(unittest.TestCase):
    def test_empty_phrases(self) -> None:
        self.assertTrue(is_empty_task_tracker("当前追踪列表没有任务"))
        self.assertTrue(is_empty_task_tracker("5 y ☆ 任务追踪？ 当前追踪列表没有任务"))
        self.assertFalse(is_empty_task_tracker("师门 买东西"))

    def test_not_empty_when_ghost(self) -> None:
        self.assertFalse(
            is_empty_task_tracker("抓鬼 大唐境外 100, 200")
        )


class TestParseTaskText(unittest.TestCase):
    def test_doc_paren_format(self) -> None:
        t = parse_task_text("前往长寿村(200,150)消灭女鬼")
        self.assertEqual(t.location, "长寿村")
        self.assertEqual(t.coordinates, (200, 150))
        self.assertEqual(t.ghost_type, "女鬼")
        self.assertTrue(t.has_target)

    def test_fullwidth_paren(self) -> None:
        t = parse_task_text("长寿村（200，150）")
        self.assertEqual(t.location, "长寿村")
        self.assertEqual(t.coordinates, (200, 150))

    def test_datang_jingwai_not_truncated(self) -> None:
        t = parse_task_text("大唐境外 123 45")
        self.assertEqual(t.location, "大唐境外")
        self.assertEqual(t.coordinates, (123, 45))

    def test_space_separated_coords(self) -> None:
        t = parse_task_text("北俱芦洲 10 20")
        self.assertEqual(t.location, "北俱芦洲")
        self.assertEqual(t.coordinates, (10, 20))

    def test_empty_raw(self) -> None:
        t = parse_task_text("")
        self.assertEqual(t.raw_text, "")
        self.assertFalse(t.has_target)

    def test_shimen_no_coords(self) -> None:
        t = parse_task_text("师门 买到风水混元丹送给师傅")
        self.assertFalse(t.has_target)


class TestGhostTaskInfo(unittest.TestCase):
    def test_has_target_coords_only(self) -> None:
        g = GhostTaskInfo(coordinates=(1, 2))
        self.assertTrue(g.has_target)
        g2 = GhostTaskInfo(coordinates=(0, 0))
        self.assertFalse(g2.has_target)


if __name__ == "__main__":
    unittest.main()

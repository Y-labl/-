"""配置加载与 live_observe 写盘（临时目录，无窗口）。"""
from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

from bot.live_observe import write_step
from bot.settings import BotSettings


class TestBotSettingsLoad(unittest.TestCase):
    def test_default_yaml_loads(self) -> None:
        root = Path(__file__).resolve().parent.parent
        cfg = BotSettings.load(root / "config" / "bot_default.yaml")
        self.assertTrue(cfg.strategy.auto_ghost_prep)
        self.assertIsInstance(cfg.live_observe.enabled, bool)
        self.assertEqual(len(cfg.roi.task_tracker), 4)


class TestLiveObserveWrite(unittest.TestCase):
    def test_manifest_jsonl(self) -> None:
        root = Path(__file__).resolve().parent.parent
        cfg = BotSettings.load(root / "config" / "bot_default.yaml")
        cfg = replace(
            cfg,
            live_observe=replace(
                cfg.live_observe,
                save_full_window=False,
                save_task_tracker_roi=False,
            ),
        )

        win = MagicMock()
        win.capture.return_value = None
        win.capture_roi_norm.return_value = None
        win.rect.return_value = (0, 0, 800, 600)
        win.hwnd_window = MagicMock()
        win.hwnd_window.title = "测试标题"

        with tempfile.TemporaryDirectory() as td:
            session = Path(td)
            write_step(
                cfg,
                win,
                session,
                0,
                "unit_test",
                round_idx=0,
                state_name="INIT",
                extra={"ok": True},
            )
            mf = session / "manifest.jsonl"
            self.assertTrue(mf.is_file())
            line = mf.read_text(encoding="utf-8").strip()
            row = json.loads(line)
            self.assertEqual(row["tag"], "unit_test")
            self.assertEqual(row["extra"]["ok"], True)


class TestRequirementDoc(unittest.TestCase):
    def test_steps_count(self) -> None:
        from bot.requirement_doc import STEPS_S21

        self.assertEqual(len(STEPS_S21), 12)
        self.assertEqual(STEPS_S21[0][0], 1)
        self.assertEqual(STEPS_S21[-1][0], 12)


if __name__ == "__main__":
    unittest.main()

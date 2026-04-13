from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GhostTaskInfo:
    task_number: int = 0
    ghost_type: str = ""
    location: str = ""
    coordinates: tuple[int, int] = (0, 0)
    ghost_king_coords: Optional[tuple[int, int]] = None
    raw_text: str = ""
    confidence: float = 0.0
    need_extra_npc: bool = False
    reward_type: str = ""

    @property
    def has_target(self) -> bool:
        """有有效游戏坐标即可寻路；地图名可由主正则或兜底坐标解析得到。"""
        return self.coordinates[0] > 0 and self.coordinates[1] > 0

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.spatial.transform import Rotation
from reachy_mini.motion.recorded_move import RecordedMove, RecordedMoves


class ActionMove:
    def __init__(self, recorded_move: RecordedMove, head_yaw_offset: float, body_yaw_offset: float):
        self.recorded_move = recorded_move
        self.head_yaw_offset = head_yaw_offset
        self.body_yaw_offset = body_yaw_offset

    @property
    def duration(self) -> float:
        return self.recorded_move.duration

    @property
    def sound_path(self):
        return self.recorded_move.sound_path

    @property
    def description(self) -> str:
        return self.recorded_move.description

    def evaluate(self, t: float):
        head, antennas, body_yaw = self.recorded_move.evaluate(t)

        # Offset head yaw
        if self.head_yaw_offset != 0:
            r = Rotation.from_matrix(head[:3, :3])
            _, _, action_yaw = r.as_euler("xyz")
            new_yaw = action_yaw + self.head_yaw_offset
            new_r = Rotation.from_euler('xyz', [0, 0, new_yaw])
            new_head = head.copy()
            new_head[:3, :3] = new_r.as_matrix()
            head = new_head

        # Offset body yaw
        if body_yaw is not None and self.body_yaw_offset != 0:
            body_yaw = body_yaw + self.body_yaw_offset

        return head, antennas, body_yaw


class ActionLibrary:
    def __init__(self, hf_dataset: str = "pollen-robotics/reachy-mini-emotions-library"):
        self.recorded_moves = RecordedMoves(hf_dataset)

    def list_moves(self) -> List[str]:
        return self.recorded_moves.list_moves()

    def get(self, name: str) -> RecordedMove:
        return self.recorded_moves.get(name)

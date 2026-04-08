import threading
import random

from reachy_mini import ReachyMini
from scipy.spatial.transform import Rotation
import numpy as np
import time

from reachy_mini_phone_teleop.action_library import ActionLibrary, ActionMove

ACTIONS = {
    "LIMP": [],
    "NO": ["no1"],
    "RESET": [],
    "SURPRISED": ["surprised1", "surprised2"],
    "HAPPY": ["success1", "cheerful1"],
    "SAD": ["sad1"],
    "ALIGN": [],
    "WAVE": ["yes1"],
    "LAUGH": ["laughing1", "laughing2"],
}

_instance: "Actions | None" = None


def init(mini: ReachyMini) -> None:
    global _instance
    _instance = Actions(mini)


def is_action_running() -> bool:
    if _instance is None:
        return False
    return _instance.is_running()


def play(action_name: str) -> None:
    if _instance is None:
        return
    _instance.play(action_name)


class Actions:
    _action_lock = threading.Lock()
    _running = False

    def __init__(self, mini: ReachyMini):
        self._mini = mini
        self._actions = ActionLibrary()
        self.reset()

    def is_running(self) -> bool:
        return self._running

    def play(self, action: str) -> None:
        if not self._action_lock.acquire(blocking=False):
            return

        self._running = True
        try:
            self.align()
            func = getattr(self, action.lower(), None)
            if not func or not callable(func):
                print(f"unknown action {action}")
                return

            func()
        finally:
            self._running = False
            self._action_lock.release()

    def align(self) -> None:
        head_pose = self._mini.get_current_head_pose()
        r = Rotation.from_matrix(head_pose[:3, :3])
        _, _, yaw = r.as_euler("xyz")
        self._mini.goto_target(body_yaw=yaw, duration=0.5)

    def _get_head_yaw(self) -> float:
        head_pose = self._mini.get_current_head_pose()
        r = Rotation.from_matrix(head_pose[:3, :3])
        _, _, yaw = r.as_euler("xyz")
        return yaw

    def _get_body_yaw(self) -> float:
        head_joints, _ = self._mini.get_current_joint_positions()
        return head_joints[0]

    def _play_dataset(self, move_name: str) -> None:
        head_yaw = self._get_head_yaw()
        body_yaw = self._get_body_yaw()
        action_move = ActionMove(self._actions.get(move_name), head_yaw, body_yaw)
        self._mini.play_move(action_move)

    def limp(self) -> None:
        self._mini.disable_motors()
        time.sleep(3)
        self._mini.enable_motors()

    def no(self) -> None:
        self._play_dataset(random.choice(ACTIONS["NO"]))

    def reset(self) -> None:
        self._mini.goto_target(head=np.eye(4), antennas=np.deg2rad([0, 0]), body_yaw=0, duration=1.0)

    def surprised(self) -> None:
        self._play_dataset(random.choice(ACTIONS["SURPRISED"]))

    def happy(self) -> None:
        self._play_dataset(random.choice(ACTIONS["HAPPY"]))

    def sad(self) -> None:
        self._play_dataset(random.choice(ACTIONS["SAD"]))

    def wave(self) -> None:
        self._play_dataset(random.choice(ACTIONS["WAVE"]))

    def laugh(self) -> None:
        self._play_dataset(random.choice(ACTIONS["LAUGH"]))

"""
Reachy Mini animations.

Usage:
    python actions.py <action>
    python actions.py --help
"""

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
from scipy.spatial.transform import Rotation
import numpy as np
import time
import random
import argparse
import threading

from reachy_mini_phone_teleop.action_library import ActionLibrary, ActionMove


_actions = None
_action_lock = threading.Lock()

def is_action_running() -> bool:
    if _action_lock.acquire(blocking=False):
        _action_lock.release()
        return False

    return True

def get_actions():
    global _actions
    if _actions is None:
        _actions = ActionLibrary()
    return _actions

# limp, reset, align are 'handmade'
CATEGORIES = {
    "LIMP": [],
    "YES": ["yes1", "yes_sad1"],
    "NO": ["no1", "no_excited1", "no_sad1"],
    "RESET": [],
    "CONFUSED": ["confused1", "lost1", "uncertain1", "curious1"],
    "WOW": ["surprised1", "surprised2"],
    "HAPPY": ["success1", "cheerful1", "enthusiastic1"],
    "SAD": ["sad1", "fear1", "scared1"],
    "ALIGN": [],
    "LAUGH": ["laughing1", "laughing2"],
}

# For backward compatibility with main.py endpoint check
ACTIONS = [
    "nod",
    "shake",
    "wave",
    "thinking",
    "sad",
    "reset",
    "align_body",
    "limp",
]


def save_state(mini):
    head_joints, antennas = mini.get_current_joint_positions()
    head_pose = mini.get_current_head_pose()
    body_yaw = head_joints[0]
    return {
        'head_joints': head_joints,
        'antennas': antennas,
        'head_pose': head_pose,
        'body_yaw': body_yaw
    }

def restore_state(mini, state):
    mini.goto_target(
        head=state['head_pose'],
        antennas=state['antennas'],
        body_yaw=None,
        duration=1.0
    )


def nod(mini: ReachyMini):
    align_body(mini)
    state = save_state(mini)
    for _ in range(2):
        mini.goto_target(head=create_head_pose(pitch=-20, degrees=True), body_yaw=None, duration=0.5)
        mini.goto_target(head=create_head_pose(pitch=20, degrees=True), body_yaw=None, duration=0.5)
    mini.goto_target(head=create_head_pose(pitch=0, degrees=True), body_yaw=None, duration=0.5)
    restore_state(mini, state)


def shake(mini: ReachyMini):
    align_body(mini)
    state = save_state(mini)
    for _ in range(2):
        mini.goto_target(head=create_head_pose(yaw=30, degrees=True), body_yaw=None, duration=0.3)
        mini.goto_target(head=create_head_pose(yaw=-30, degrees=True), body_yaw=None, duration=0.3)
    mini.goto_target(head=create_head_pose(yaw=0, degrees=True), body_yaw=None, duration=0.3)
    restore_state(mini, state)


def wave(mini: ReachyMini):
    align_body(mini)
    state = save_state(mini)
    for _ in range(3):
        mini.goto_target(antennas=np.deg2rad([-45, 45]), body_yaw=None, duration=0.3)
        mini.goto_target(antennas=np.deg2rad([45, -45]), body_yaw=None, duration=0.3)
    mini.goto_target(antennas=np.deg2rad([0, 0]), body_yaw=None, duration=0.3)
    restore_state(mini, state)


def thinking(mini: ReachyMini):
    align_body(mini)
    state = save_state(mini)
    mini.goto_target(head=create_head_pose(roll=30, degrees=True), body_yaw=None, duration=2.0)
    time.sleep(2.0)
    mini.goto_target(head=create_head_pose(roll=0, degrees=True), body_yaw=None, duration=0.8)
    restore_state(mini, state)


def sad(mini: ReachyMini):
    align_body(mini)
    state = save_state(mini)
    mini.goto_target(head=create_head_pose(pitch=30, degrees=True), antennas=np.deg2rad([-170, 170]), body_yaw=None, duration=1.0)
    time.sleep(4.0)
    mini.goto_target(head=create_head_pose(pitch=0, degrees=True), antennas=np.deg2rad([0, 0]), body_yaw=None, duration=1.0)
    restore_state(mini, state)


def reset(mini: ReachyMini) -> None:
    mini.goto_target(head=np.eye(4), antennas=np.deg2rad([0, 0]), body_yaw=0, duration=1.0)


def align_body(mini: ReachyMini) -> None:
    head_pose = mini.get_current_head_pose()
    r = Rotation.from_matrix(head_pose[:3, :3])
    _, _, yaw = r.as_euler("xyz")
    mini.goto_target(body_yaw=yaw, duration=0.5)
    time.sleep(0.5)


def limp(mini: ReachyMini):
    mini.disable_motors()
    time.sleep(3)
    mini.enable_motors()


def play_category(mini: ReachyMini, category: str) -> None:
    """Play a random action from the specified category."""
    if not _action_lock.acquire(blocking=False):
        return  # Already running, skip
    
    try:
        if category not in CATEGORIES:
            print(f"Unknown category: {category}")
            return
        
        action_list = CATEGORIES[category]
        
        # Handle special categories that use existing functions
        if category == "LIMP":
            limp(mini)
            return
        if category == "RESET":
            reset(mini)
            return
        if category == "ALIGN":
            align_body(mini)
            return
        
        # For HuggingFace actions
        if not action_list:
            print(f"No actions defined for category: {category}")
            return
        
        actions = get_actions()
        move_name = random.choice(action_list)
        align_body(mini)
        head_joints, _ = mini.get_current_joint_positions()
        current_body_yaw = head_joints[0]
        head_pose = mini.get_current_head_pose()
        r = Rotation.from_matrix(head_pose[:3, :3])
        _, _, current_head_yaw = r.as_euler("xyz")
        action_move = ActionMove(actions.get(move_name), current_head_yaw, current_body_yaw)
        state = save_state(mini)
        mini.play_move(action_move)
        restore_state(mini, state)
    finally:
        _action_lock.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reachy Mini animations")
    parser.add_argument("action", choices=ACTIONS, help="Animation to play")

    args = parser.parse_args()
    func = globals()[args.action]

    with ReachyMini() as mini:
        func(mini)


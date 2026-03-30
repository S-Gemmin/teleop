import threading

import numpy as np
from reachy_mini.utils import create_head_pose

from reachy_mini_phone_teleop.logger import Logger
from reachy_mini_phone_teleop.constants import (
	CONTROL_HZ,
	ROTATION_LIMIT,
	ROTATION_SCALE,
	ROTATION_SMOOTHING_ALPHA,
	ROTATION_DEADBAND,
	ANTENNA_CLIP_RANGE,
	ANTENNA_SMOOTHING_ALPHA,
	ANTENNA_DEADBAND,
	BODY_YAW_LIMIT,
	BODY_YAW_TURN_RATE,
)


def smooth(prev: np.ndarray, new: np.ndarray | None, alpha: float) -> np.ndarray:
	return prev + alpha * (new - prev)

def deadband(prev: np.ndarray, new: np.ndarray, threshold: float | np.ndarray) -> np.ndarray:
	delta = new - prev
	return np.where(np.abs(delta) < threshold, prev, new)

class TeleopController:
	def __init__(self, logger: Logger | None = None):
		self._logger = logger
		self._state_lock = threading.Lock()
		self.rotation = np.zeros(3)
		self.antennas = np.zeros(2)
		self.body_yaw = 0.0
		self._turn_left = False
		self._turn_right = False
		self._action_running = False

	@property
	def action_running(self) -> bool:
		return self._action_running

	@action_running.setter
	def action_running(self, value: bool) -> None:
		self._action_running = value

	def update(self, mini) -> None:  # type: ignore[no-untyped-def]
		if self._action_running:
			return

		with self._state_lock:
			rotation = self.rotation.copy()
			antennas = self.antennas.copy()

		# feat: align-btn, so we don't need this anymore
		# self._update_body_yaw()
		# body_yaw = self.body_yaw

		head = create_head_pose(roll=rotation[0], pitch=rotation[1], yaw=rotation[2], degrees=False)
		mini.set_target(head=head, antennas=antennas)

	def _update_body_yaw(self) -> None:
		interval = 1.0 / CONTROL_HZ
		with self._state_lock:
			turn_left = self._turn_left
			turn_right = self._turn_right
			body_yaw = self.body_yaw

		if turn_left and not turn_right:
			body_yaw = min(body_yaw + BODY_YAW_TURN_RATE * interval, BODY_YAW_LIMIT)
		elif turn_right and not turn_left:
			body_yaw = max(body_yaw - BODY_YAW_TURN_RATE * interval, -BODY_YAW_LIMIT)

		self.body_yaw = body_yaw

	def process_message(self, message: dict) -> None:
		if not isinstance(message, dict):
			return

		self._update_antennas(message)
		self._update_head_rotation(message)
		self._update_turn_signals(message)

		if self._logger:
			self._log_state(message)

	def _update_turn_signals(self, message: dict) -> None:
		if "turnLeft" not in message and "turnRight" not in message:
			return

		with self._state_lock:
			self._turn_left = message.get("turnLeft", False)
			self._turn_right = message.get("turnRight", False)

	def _update_antennas(self, message: dict) -> None:
		if "antennas" not in message:
			return

		right_joystick_input = message.get("rightJoystickInput", False)
		left_joystick_input = message.get("leftJoystickInput", False)
		new_antenna = np.array(message.get("antennas"))
		new_antenna = np.clip(new_antenna, -ANTENNA_CLIP_RANGE, ANTENNA_CLIP_RANGE)

		if right_joystick_input:
			new_antenna[0] = smooth(self.antennas[0], new_antenna[0], ANTENNA_SMOOTHING_ALPHA)
			self.antennas[0] = deadband(self.antennas[0], new_antenna[0], ANTENNA_DEADBAND)
		if left_joystick_input:
			new_antenna[1] = smooth(self.antennas[1], new_antenna[1], ANTENNA_SMOOTHING_ALPHA)
			self.antennas[1] = deadband(self.antennas[1], new_antenna[1], ANTENNA_DEADBAND)

	def _update_head_rotation(self, message: dict) -> None:
		if "head" not in message:
			return

		head = np.array(message.get("head", [0, 0, 0]))
		new_rotation = np.clip(ROTATION_SCALE * head, -ROTATION_LIMIT, ROTATION_LIMIT)
		new_rotation = smooth(self.rotation, new_rotation, ROTATION_SMOOTHING_ALPHA)
		self.rotation = deadband(self.rotation, new_rotation, ROTATION_DEADBAND)

	def _log_state(self, message: dict) -> None:
		with self._state_lock:
			self._logger.log({
				"rotation": self.rotation.tolist(),
				"antennas": self.antennas.tolist(),
			})

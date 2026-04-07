import argparse
import multiprocessing as mp
import os
import threading
import time
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

import numpy as np
from fastapi import status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import teleop
from fastapi.staticfiles import StaticFiles
from reachy_mini import ReachyMini, ReachyMiniApp
from teleop import Teleop

from reachy_mini_phone_teleop.camera import CameraStreaming
from reachy_mini_phone_teleop.controller import TeleopController
from reachy_mini_phone_teleop.logger import Logger
from reachy_mini_phone_teleop.constants import CONTROL_HZ
from reachy_mini_phone_teleop import actions


class ReachyMiniPhoneTeleop(ReachyMiniApp):
	custom_app_url = "https://0.0.0.0:8042"
	dont_start_webserver: bool = True
	_web_root: Path = Path(__file__).parent / "web"

	def __init__(self, logger: Logger | None = None):
		self.request_media_backend = "default"
		super().__init__()

		self._logger = logger
		self._stop_event: threading.Event | None = None
		self._control_thread: threading.Thread | None = None
		self._controller = TeleopController(logger=logger)
		self._camera = CameraStreaming()
		self._mini: ReachyMini | None = None

	@staticmethod
	def _remove_default_route(app) -> None:
		filtered = []

		for r in app.router.routes:
			path = getattr(r, "path", None)
			methods = getattr(r, "methods", set())
			if not (path == "/" and methods == {"GET"}):
				filtered.append(r)

		app.router.routes = filtered

	def _attach_custom_ui(self, teleop_instance: Teleop, mini: ReachyMini) -> None:
		self._mini = mini
		app = teleop_instance._Teleop__app

		if self._web_root.is_dir():
			self._remove_default_route(app)

			static_dir = str(self._web_root)
			app.mount("/static", StaticFiles(directory=static_dir), name="static")

			teleop_assets_dir = os.path.join(os.path.dirname(teleop.__file__), "assets")

			if os.path.exists(teleop_assets_dir):
				filtered = []

				for r in app.router.routes:
					path = getattr(r, "path", None)
					if path != "/assets":
						filtered.append(r)

				app.router.routes = filtered
				app.mount("/assets", StaticFiles(directory=teleop_assets_dir), name="assets")

			@app.get("/")
			async def index():
				return FileResponse(str(self._web_root / "index.html"))

			@app.get("/video_feed")
			async def video_feed():
				frame_gen = self._camera.generate_mjpeg()
				media_type = "multipart/x-mixed-replace; boundary=frame"
				return StreamingResponse(frame_gen, media_type=media_type)
			
			@app.get("/ping")
			async def ping():
				return JSONResponse({"pong": time.time()})

		@app.post("/action/{action_name}")
		async def run_action(action_name: str):
			if actions.is_action_running():
				return JSONResponse(
					{"error": "action already running"},
					status_code=409
				)
			
			if action_name not in actions.CATEGORIES:
				return JSONResponse(
					{"error": f"Unknown category: {action_name}. Use play_category() with: {list(actions.CATEGORIES.keys())}"},
					status_code=status.HTTP_400_BAD_REQUEST,
				)

			self._controller.action_running = True
			
			def execute():
				try:
					actions.play_category(mini, action_name)
				finally:
					self._controller.action_running = False
			
			threading.Thread(target=execute, daemon=True).start()
			return JSONResponse({"status": "started", "category": action_name})

		@app.get("/robot_state")
		async def get_robot_state():
			mini = self._mini
			if mini is None:
				return JSONResponse({"error": "Robot not initialized"}, status_code=500)
			head_joints, antennas = mini.get_current_joint_positions()
			head_pose = mini.get_current_head_pose()
			return {
				'head_joints': list(head_joints),
				'antennas_position': list(antennas),
				'head_pose': head_pose.flatten().tolist(),
				'body_yaw': head_joints[0]
			}

	def _control_loop(self, mini: ReachyMini, stop_event: threading.Event) -> None:
		actions.reset(mini)
		time.sleep(0.1)

		interval = 1.0 / CONTROL_HZ

		while not stop_event.is_set():
			t_start = time.monotonic()

			try:
				self._controller.update(mini)
			except Exception:
				break

			elapsed = time.monotonic() - t_start
			sleep_time = interval - elapsed
			if sleep_time > 0:
				time.sleep(sleep_time)

	def run(self, mini: ReachyMini, stop_event: threading.Event):
		self._stop_event = stop_event

		if mini.media is not None:
			self._camera.start(mini.media)
			print("Camera streaming started")

		self._control_thread = threading.Thread(
			target=self._control_loop,
            args=(mini, stop_event)
		)
		self._control_thread.start()

		def callback(pose: np.ndarray, message: dict) -> None:
			self._controller.process_message(message)

		parsed = urlparse(self.custom_app_url)
		port = parsed.port or 8042
		teleop_inst = Teleop(port=port)

		self._attach_custom_ui(teleop_inst, mini)
		teleop_inst.subscribe(callback)
		teleop_inst.run()

	def stop(self):
		if self._stop_event:
			self._stop_event.set()
		if self._control_thread and self._control_thread.is_alive():
			self._control_thread.join(timeout=1.0)
		if self._logger:
			self._logger.close()
		self._camera.stop()
		super().stop()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Reachy Mini Phone Teleop")
	parser.add_argument("--record", action="store_true", help="Enable data logging")
	args = parser.parse_args()

	logger = None
	if args.record:
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		output_path = f"data/control_logs/{timestamp}.jsonl"
		logger = Logger(output_path)
		print(f"Recording to: {output_path}")

	mp.set_start_method("spawn", force=True)
	app = ReachyMiniPhoneTeleop(logger=logger)
	try:
		app.wrapped_run()
	except Exception as e:
		print(e)
		app.stop()

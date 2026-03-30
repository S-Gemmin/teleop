import threading
import time
import cv2


class CameraStreaming:
	def __init__(self, target_fps: int = 20, jpeg_quality: int = 75):
		self._target_fps = target_fps
		self._jpeg_quality = jpeg_quality
		self._frame_lock = threading.Lock()
		self._latest_frame = None
		self._frame_thread = None
		self._frame_stop_event = None
		self._warned_frame_none = False

	def start(self, media) -> None:
		self._frame_stop_event = threading.Event()
		self._frame_thread = threading.Thread(
			target=self._capture_frames,
            args=(media,),
            daemon=True
		)
		self._frame_thread.start()

	def stop(self) -> None:
		if self._frame_stop_event:
			self._frame_stop_event.set()
		if self._frame_thread:
			self._frame_thread.join(timeout=2)

	def _capture_frames(self, media) -> None:
		frame_interval = 1.0 / self._target_fps

		while not self._frame_stop_event.is_set():
			t_start = time.monotonic()

			try:
				frame = media.get_frame()
				if frame is not None:
					_, encoded = cv2.imencode(
						".jpg",
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
					)
					jpeg_bytes = encoded.tobytes()

					with self._frame_lock:
						self._latest_frame = jpeg_bytes
				elif not self._warned_frame_none:
					print("get_frame() returned None")
					self._warned_frame_none = True
			except Exception as e:
				print(e)

			elapsed = time.monotonic() - t_start
			sleep_time = frame_interval - elapsed
			if sleep_time > 0:
				time.sleep(sleep_time)

	def generate_mjpeg(self):
		frame_interval = 1.0 / self._target_fps

		while True:
			with self._frame_lock:
				frame = self._latest_frame

			if frame is not None:
				yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

			time.sleep(frame_interval)

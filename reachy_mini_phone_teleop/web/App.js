import { SceneManager } from './SceneManager.js';
import { RobotManager } from './RobotManager.js';
import { JoystickController } from './JoystickController.js';
import { ActionHandler } from './ActionHandler.js';
import {
	quaternionToEuler,
	invertQuaternion,
	multiplyQuaternion,
	computeOrientation,
} from './Orientation.js';

const videoBackground = document.getElementById("video-background");
const videoError = document.getElementById("video-error");
const headToggle = document.getElementById("head-toggle");
const pingDisplay = document.getElementById("ping-display");
const fullscreenBtn = document.getElementById("fullscreen-btn");
const robotViewer = document.getElementById("robot-viewer");

class TeleopApp {
	constructor() {
		this.state = {
			roll: 0,
			pitch: 0,
			yaw: 0,
			leftAntenna: 0,
			rightAntenna: 0,
			headActive: false,
			connected: false,
			baselineQuaternion: null,
			actionRunning: false,
			turnLeft: false,
			turnRight: false,
			keysPressed: {},
			mode: null,
		};

		this.leftJoystick = null;
		this.rightJoystick = null;
	}

	startApp(mode) {
		document.getElementById("mode-select").style.display = "none";
		this.state.mode = mode;

		if (mode === "laptop") {
			this.initVideo();
		} else {
			this.initJoysticks();
		}

		this.wsProtocol = location.protocol === "https:" ? "wss:" : "ws:";
		this.socket = new WebSocket(this.wsProtocol + "//" + location.host + "/ws");
		this.socket.onopen = () => (this.state.connected = true);
		this.socket.onclose = () => (this.state.connected = false);
		this.socket.onerror = () => (this.state.connected = false);
		this.lastFrameTime = performance.now();

		this.actionHandler = new ActionHandler({
			onActionStart: () => {
				this.state.actionRunning = true;
				this.state.headActive = false;
				headToggle.classList.remove("active");
			},
			onActionEnd: () => {
				this.state.actionRunning = false;
			},
			onHeadToggle: () => {
				this.state.headActive = !this.state.headActive;
				headToggle.classList.toggle("active", this.state.headActive);
			},
			onTurnLeft: (value) => {
				this.state.turnLeft = value;
				if (this.state.turnLeft && this.state.turnRight) {
					this.state.turnLeft = false;
					this.state.turnRight = false;
				}
			},
			onTurnRight: (value) => {
				this.state.turnRight = value;
				if (this.state.turnLeft && this.state.turnRight) {
					this.state.turnLeft = false;
					this.state.turnRight = false;
				}
			},
		});

		this.initFullscreen();
		this.initKeyboard();
		this.actionHandler.init(headToggle);
		if (mode === "mobile") this.initDeviceOrientation();
		this.startPing();
		if (mode === "laptop") this.initRobotViewer();
		this.loop();
	}

	async measurePing() {
		try {
			const start = performance.now();
			await fetch("/ping");
			const ping = Math.round(performance.now() - start);
			pingDisplay.textContent = ping > 0 ? "P:" + ping + "ms" : "P:--";
		} catch (e) {
			pingDisplay.textContent = "P:--";
		}
	}

	initVideo() {
		videoBackground.style.display = "block";
		videoBackground.src = "/video_feed";
		videoError.style.display = "none";
	}

	initJoysticks() {
		this.leftJoystick = new JoystickController(document.getElementById("left"));
		this.rightJoystick = new JoystickController(document.getElementById("right"));
	}

	initFullscreen() {
		fullscreenBtn.addEventListener("click", () => {
			const elem = document.documentElement;
			if (!document.fullscreenElement) {
				elem.requestFullscreen?.() || elem.webkitRequestFullScreen?.() || elem.mozRequestFullScreen?.();
				robotViewer.style.display = "block";
			} else {
				document.exitFullscreen?.();
				robotViewer.style.display = "none";
			}
		});

		document.addEventListener("fullscreenchange", () => {
			if (!document.fullscreenElement) {
				robotViewer.style.display = "none";
			}
		});
	}

	initKeyboard() {
		document.addEventListener("keydown", (e) => {
			this.state.keysPressed[e.key.toLowerCase()] = true;
		});

		document.addEventListener("keyup", (e) => {
			this.state.keysPressed[e.key.toLowerCase()] = false;
		});
	}

	initDeviceOrientation() {
		window.addEventListener("deviceorientation", (e) => {
			if (!this.state.headActive) return;

			const q = computeOrientation(e.alpha, e.beta, e.gamma);

			if (!this.state.baselineQuaternion) this.state.baselineQuaternion = q;
			const delta = multiplyQuaternion(invertQuaternion(this.state.baselineQuaternion), q);
			const euler = quaternionToEuler(delta);

			this.state.roll = -euler.pitch;
			this.state.pitch = euler.roll;
			this.state.yaw = euler.yaw;
		});
	}

	startPing() {
		setInterval(() => this.measurePing(), 1000);
	}

	loop() {
		if (this.state.mode !== "mobile") {
			requestAnimationFrame(() => this.loop());
			return;
		}

		const now = performance.now();
		const dt = (now - this.lastFrameTime) / 1000;
		this.lastFrameTime = now;

		const left = this.leftJoystick.getPosition();
		const right = this.rightJoystick.getPosition();
		const leftActive = this.leftJoystick.isActive();
		const rightActive = this.rightJoystick.isActive();

		if (rightActive) this.state.rightAntenna = Math.atan2(-right.x, -right.y);
		if (leftActive) this.state.leftAntenna = Math.atan2(-left.x, -left.y);

		const keys = this.state.keysPressed;
		const ROLL_RATE = 1.0;
		const PITCH_RATE = 1.0;
		const YAW_RATE = 0.5;
		const rollDelta = ((keys['q'] ? 1 : 0) - (keys['e'] ? 1 : 0)) * ROLL_RATE * dt;
		const pitchDelta = ((keys['s'] ? 1 : 0) - (keys['w'] ? 1 : 0)) * PITCH_RATE * dt;
		const yawDelta = ((keys['d'] ? 1 : 0) - (keys['a'] ? 1 : 0)) * YAW_RATE * dt;

		this.state.roll += rollDelta;
		this.state.pitch += pitchDelta;
		this.state.yaw += yawDelta;

		if (this.state.connected && this.socket.readyState === WebSocket.OPEN && !this.state.actionRunning) {
			this.socket.send(
				JSON.stringify({
					type: "pose",
					data: {
						position: { x: 0, y: 0, z: 0 },
						orientation: { x: 0, y: 0, z: 0, w: 1 },
						move: false,
						leftJoystickInput: leftActive,
						rightJoystickInput: rightActive,
						antennas: [this.state.rightAntenna, this.state.leftAntenna],
						head: [this.state.roll, this.state.pitch, this.state.yaw],
						turnLeft: this.state.turnLeft,
						turnRight: this.state.turnRight,
					},
				})
			);
		}

		requestAnimationFrame(() => this.loop());
	}

	async initRobotViewer() {
		const viewerContainer = document.getElementById("robot-viewer");
		if (!viewerContainer) return;

		const sceneManager = new SceneManager(viewerContainer);
		const robotManager = new RobotManager(() => {}, sceneManager.envMap);

		try {
			const robot = await robotManager.loadRobot();
			sceneManager.add(robot);
			sceneManager.animate();

			setInterval(async () => {
				try {
					const response = await fetch("/robot_state");
					const data = await response.json();
					robotManager.updateJoints(data);
				} catch (e) {
					console.error("Failed to fetch robot state:", e);
				}
			}, 100);
		} catch (e) {
			console.error("Failed to load robot:", e);
			viewerContainer.style.display = "none";
		}
	}

	run() {
	}
}

const app = new TeleopApp();
app.run();

window.startLaptopMode = () => app.startApp("laptop");
window.startMobileMode = () => app.startApp("mobile");

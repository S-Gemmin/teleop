export class JoystickController {
	constructor(root) {
		this.root = root;
		this.handle = root.querySelector(".handle");
		this.center = { x: 0, y: 0 };
		this.maxDist = 0;
		this.activeId = null;
		this.x = 0;
		this.y = 0;
		this.mouseActive = false;

		this._initGeometry();
		this._initTouch();
		this._initMouse();

		window.addEventListener("resize", () => this._initGeometry());
		window.addEventListener("orientationchange", () => this._initGeometry());
	}

	_initGeometry() {
		const rootRect = this.root.getBoundingClientRect();
		const handleRect = this.handle.getBoundingClientRect();
		this.center.x = rootRect.left + rootRect.width / 2;
		this.center.y = rootRect.top + rootRect.height / 2;
		this.maxDist = (rootRect.width - handleRect.width) / 2;
	}

	_reset() {
		this.x = 0;
		this.y = 0;
		this.handle.style.transform = "translate(-50%,-50%)";
		this.root.classList.remove("active");
	}

	_updatePosition(clientX, clientY) {
		let dx = clientX - this.center.x;
		let dy = clientY - this.center.y;
		const dist = Math.hypot(dx, dy);
		if (dist > this.maxDist) {
			dx = (dx / dist) * this.maxDist;
			dy = (dy / dist) * this.maxDist;
		}
		this.x = dx / this.maxDist;
		this.y = dy / this.maxDist;
		this.handle.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
	}

	_endTouch(touches) {
		for (const t of touches) {
			if (t.identifier === this.activeId) {
				this.activeId = null;
				this._reset();
			}
		}
	}

	_initTouch() {
		this.root.addEventListener("touchstart", (e) => {
			e.preventDefault();
			for (const t of e.changedTouches) {
				if (this.activeId === null) {
					this.activeId = t.identifier;
					this.root.classList.add("active");
					this._updatePosition(t.clientX, t.clientY);
				}
			}
		});

		this.root.addEventListener("touchmove", (e) => {
			e.preventDefault();
			for (const t of e.changedTouches) {
				if (t.identifier === this.activeId) {
					this._updatePosition(t.clientX, t.clientY);
				}
			}
		});

		this.root.addEventListener("touchend", (e) => {
			e.preventDefault();
			this._endTouch(e.changedTouches);
		});
		this.root.addEventListener("touchcancel", (e) => {
			e.preventDefault();
			this._endTouch(e.changedTouches);
		});
	}

	_initMouse() {
		this.root.addEventListener("mousedown", (e) => {
			e.preventDefault();
			this.mouseActive = true;
			this.root.classList.add("active");
			this._updatePosition(e.clientX, e.clientY);
		});

		const endMouse = () => {
			if (this.mouseActive) {
				this.mouseActive = false;
				this._reset();
			}
		};
		document.addEventListener("mousemove", (e) => {
			if (this.mouseActive) this._updatePosition(e.clientX, e.clientY);
		});
		document.addEventListener("mouseup", endMouse);
		document.addEventListener("mouseleave", endMouse);
	}

	getPosition() {
		return { x: this.x, y: this.y };
	}

	isActive() {
		return this.activeId !== null || this.mouseActive;
	}
}

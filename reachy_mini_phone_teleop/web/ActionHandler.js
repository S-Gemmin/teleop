export class ActionHandler {
	constructor(options) {
		this.onActionStart = options.onActionStart || (() => {});
		this.onActionEnd = options.onActionEnd || (() => {});
		this.onHeadToggle = options.onHeadToggle || (() => {});
		this.onTurnLeft = options.onTurnLeft || (() => {});
		this.onTurnRight = options.onTurnRight || (() => {});
	}

	init(headToggleElement) {
		this._initActionButtons();
		this._initTurnButtons();
		this._initHeadToggle(headToggleElement);
	}

	async _handleAction(btn) {
		const action = btn.dataset.action;
		if (!action) return;

		this.onActionStart();
		btn.disabled = true;

		try {
			await fetch("/action/" + action, { method: "POST" });
		} catch (e) {
			console.error("Action failed:", e);
		}

		btn.disabled = false;
		this.onActionEnd();
	}

	_initActionButtons() {
		document.querySelectorAll(".action-btn").forEach((btn) => {
			btn.addEventListener("click", async () => {
				await this._handleAction(btn);
			});
		});
	}

	_initTurnButtons() {
		document.querySelectorAll(".turn-btn").forEach((btn) => {
			const turnDir = btn.dataset.turn;
			const isLeft = turnDir === "left";

			const setTurn = (value) => {
				if (isLeft) {
					this.onTurnLeft(value);
				} else {
					this.onTurnRight(value);
				}
			};

			btn.addEventListener("touchstart", (e) => {
				e.preventDefault();
				setTurn(true);
			});
			btn.addEventListener("touchend", (e) => {
				e.preventDefault();
				setTurn(false);
			});
			btn.addEventListener("touchcancel", (e) => {
				e.preventDefault();
				setTurn(false);
			});
		});
	}

	_initHeadToggle(headToggleElement) {
		if (!headToggleElement) return;

		headToggleElement.addEventListener("touchstart", (e) => {
			e.preventDefault();
			this.onHeadToggle();
		});
	}
}

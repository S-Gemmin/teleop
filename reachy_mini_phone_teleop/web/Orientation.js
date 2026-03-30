export function quaternionToEuler(q) {
	const sinr_cosp = 2 * (q.w * q.x + q.y * q.z);
	const cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y);
	const roll = Math.atan2(sinr_cosp, cosr_cosp);

	const sinp = 2 * (q.w * q.y - q.z * q.x);
	const pitch = Math.abs(sinp) >= 1 ? (Math.sign(sinp) * Math.PI) / 2 : Math.asin(sinp);

	const siny_cosp = 2 * (q.w * q.z + q.x * q.y);
	const cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z);
	const yaw = Math.atan2(siny_cosp, cosy_cosp);

	return { roll, pitch, yaw };
}

export function invertQuaternion(q) {
	return { x: -q.x, y: -q.y, z: -q.z, w: q.w };
}

export function multiplyQuaternion(a, b) {
	return {
		w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
		x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
		y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
		z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
	};
}

export function computeOrientation(alpha, beta, gamma) {
	const d2r = Math.PI / 180;
	const a = alpha * d2r;
	const b = beta * d2r;
	const g = gamma * d2r;

	const c1 = Math.cos(a / 2), s1 = Math.sin(a / 2);
	const c2 = Math.cos(b / 2), s2 = Math.sin(b / 2);
	const c3 = Math.cos(g / 2), s3 = Math.sin(g / 2);

	return {
		w: c1 * c2 * c3 - s1 * s2 * s3,
		x: s1 * s2 * c3 + c1 * c2 * s3,
		y: s1 * c2 * c3 + c1 * s2 * s3,
		z: c1 * s2 * c3 - s1 * c2 * s3,
	};
}

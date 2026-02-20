/* =======================
   SEND COMMAND (Flask)
======================= */
async function sendCommand(endpoint, data = {}) {
    try {
        const formData = new FormData();
        for (const [k, v] of Object.entries(data)) {
            formData.append(k, v);
        }

        const res = await fetch(`/${endpoint}`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error(res.status);
        const txt = await res.text();
        log(`[server] ${endpoint}: ${txt}`);
        return txt;
    } catch (e) {
        log(`[error] ${endpoint}: ${e.message}`);
    }
}

/* =======================
   THEME TOGGLE
======================= */
const rootHtml = document.documentElement;
const themeToggle = document.getElementById('themeToggle');
themeToggle.addEventListener('change', () => {
    rootHtml.setAttribute(
        'data-bs-theme',
        themeToggle.checked ? 'light' : 'dark'
    );
});

/* =======================
   CLOCK
======================= */
const clock = document.getElementById('clock');
function tick() {
    const d = new Date();
    const p = n => String(n).padStart(2, '0');
    clock.textContent =
        `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())} | ` +
        `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}
setInterval(tick, 1000);
tick();

/* =======================
   MODE SWITCH
======================= */
document.querySelectorAll('[data-mode]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('[data-mode]')
            .forEach(b => b.classList.remove('active'));
        document.querySelectorAll(`[data-mode="${btn.dataset.mode}"]`)
            .forEach(b => b.classList.add('active'));

        log(`[mode] ${btn.dataset.mode}`);
        sendCommand('mode', { mode: btn.dataset.mode });
    });
});

/* =======================
   JOYSTICK (FIXED)
======================= */
const base = document.getElementById('joyBase');
const thumb = document.getElementById('joyThumb');
const speedRing = document.getElementById('speedRing');

let dragging = false;
let center = { x: 0, y: 0 };
let radius = 0;

function setupJoy() {
    const r = base.getBoundingClientRect();
    center.x = r.left + r.width / 2;
    center.y = r.top + r.height / 2;
    radius = r.width / 2 - 22; // compensation for thumb size
}

function handleMove(x, y) {
    const dx = x - center.x;
    const dy = y - center.y;

    const dist = Math.min(Math.hypot(dx, dy), radius);
    const angle = Math.atan2(dy, dx);

    const px = Math.cos(angle) * dist;
    const py = Math.sin(angle) * dist;

    thumb.style.transform =
        `translate(-50%, -50%) translate(${px}px, ${py}px)`;

    const vx = (px / radius).toFixed(2);
    const vy = (py / radius).toFixed(2);
    const speed = Math.round((dist / radius) * 100);

    speedRing.dataset.speed = speed;

    sendCommand('joystick', { vx, vy, speed });
}

thumb.addEventListener('pointerdown', e => {
    setupJoy();
    dragging = true;
    thumb.setPointerCapture(e.pointerId);
});

window.addEventListener('pointermove', e => {
    if (!dragging) return;
    handleMove(e.clientX, e.clientY);
});

window.addEventListener('pointerup', () => {
    if (!dragging) return;
    dragging = false;

    thumb.style.transform = 'translate(-50%, -50%)';
    speedRing.dataset.speed = 0;

    sendCommand('joystick', { vx: 0, vy: 0, speed: 0 });
    log('[joy] released');
});

/* =======================
   PTZ
======================= */
const ptz = dir => {
    log(`[ptz] ${dir}`);
    sendCommand('ptz', { direction: dir });
};

['Up', 'Down', 'Left', 'Right', 'Center']
    .forEach(k => {
        document.getElementById('ptz' + k).onclick =
            () => ptz(k.toLowerCase());
    });

document.getElementById('zoomIn').onclick = () => ptz('zoom_in');
document.getElementById('zoomOut').onclick = () => ptz('zoom_out');

/* =======================
   EMERGENCY STOP
======================= */
document.getElementById('btnStop').onclick = () => {
    log('[stop] EMERGENCY STOP');
    sendCommand('emergency_stop');
};

/* =======================
   BATTERY
======================= */
function setBattery(p) {
    p = Math.max(0, Math.min(100, p));
    const circ = 2 * Math.PI * 42;
    const dash = (p / 100) * circ;

    document.getElementById('batteryArc')
        .setAttribute('stroke-dasharray', `${dash} ${circ - dash}`);
    document.getElementById('batteryText').textContent = `${p}%`;
}
setBattery(78);

/* =======================
   LOG
======================= */
const logBox = document.getElementById('logBox');
function log(msg) {
    const ts = new Date().toLocaleTimeString();
    logBox.textContent += `\n[${ts}] ${msg}`;
    logBox.scrollTop = logBox.scrollHeight;
}
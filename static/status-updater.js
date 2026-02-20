class StatusUpdater {
    constructor() {
        this.statusUrl = '/check_status';
        this.pollingInterval = 1000; // هر 1 ثانیه
        this.init();
    }

    init() {
        // اولین بار وضعیت را بگیر
        this.fetchStatus();

        // polling تنظیم
        setInterval(() => this.fetchStatus(), this.pollingInterval);
    }

    async fetchStatus() {
        try {
            const response = await fetch(this.statusUrl);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            this.updateUI(data);
        } catch (error) {
            console.error('Error fetching status:', error);
            this.showError();
        }
    }

    updateUI(data) {
        // به‌روزرسانی باتری
        this.updateBattery(data.battery);

        // به‌روزرسانی لینک
        this.updateLink(data.link);

        // به‌روزرسانی سنسورهای IR
        this.updateIRSensors(data.ir_sensors);
    }

    updateBattery(level) {
        // به‌روزرسانی متن
        document.getElementById('batteryText').textContent = `${level}%`;

        // به‌روزرسانی نمودار گِیج
        const arc = document.getElementById('batteryArc');
        const circumference = 2 * Math.PI * 42; // محیط دایره
        const dashLength = (level / 100) * circumference;
        arc.style.strokeDasharray = `${dashLength} ${circumference}`;

        // تغییر رنگ بر اساس سطح باتری
        if (level > 30) {
            arc.style.stroke = 'var(--ok)';
        } else {
            arc.style.stroke = 'var(--warn)';
        }
    }

    updateLink(linkType) {
        const linkElement = document.getElementById('linkText');
        linkElement.textContent = linkType;
    }

    updateIRSensors(sensors) {
        // برای هر سنسور
        const sensorElements = {
            'left': document.querySelector('.chip:nth-child(1) .badge'),
            'center': document.querySelector('.chip:nth-child(2) .badge'),
            'right': document.querySelector('.chip:nth-child(3) .badge')
        };

        // به‌روزرسانی رنگ‌ها
        Object.keys(sensors).forEach(sensor => {
            const element = sensorElements[sensor];
            if (!element) return;

            switch (sensors[sensor]) {
                case 1:
                    element.style.background = 'var(--ok)';
                    break;
                case 0:
                    element.style.background = 'var(--warn)';
                    break;
            }
        });
    }

    showError() {
        console.warn('Unable to fetch status');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const statusUpdater = new StatusUpdater();
});
/* ===== Time Manager ===== */

const TimerModule = {
  countdown: { h: 0, m: 0, s: 0, remaining: 0, running: false, interval: null },
  alarms: [],
  calYear: new Date().getFullYear(),
  calMonth: null,
  events: {},

  init() {
    // View switching
    document.querySelectorAll('[data-timer-view]').forEach(btn => {
      btn.addEventListener('click', () => this.switchView(btn.dataset.timerView));
    });

    this.initCountdown();
    this.initAlarm();
    this.initCalendar();
  },

  switchView(view) {
    document.getElementById('timerHome').classList.add('hidden');
    document.getElementById('atlantisTimer').classList.add('hidden');
    document.getElementById('alarmView').classList.add('hidden');
    document.getElementById('calendarView').classList.add('hidden');

    if (view === 'home') document.getElementById('timerHome').classList.remove('hidden');
    if (view === 'countdown') { document.getElementById('atlantisTimer').classList.remove('hidden'); this.renderScrolls(); }
    if (view === 'alarm') { document.getElementById('alarmView').classList.remove('hidden'); this.renderAlarms(); }
    if (view === 'calendar') { document.getElementById('calendarView').classList.remove('hidden'); this.renderCalendarMonths(); }
  },

  /* ===== Countdown ===== */
  initCountdown() {
    this.initScrolls();
    document.getElementById('atlantisCityBtn').addEventListener('click', () => {
      if (!this.countdown.running) {
        const total = this.countdown.h * 3600 + this.countdown.m * 60 + this.countdown.s;
        if (total === 0) return;
        this.startCountdown(total);
      } else {
        this.pauseCountdown();
      }
    });
  },

  initScrolls() {
    const scrollDefs = [
      { el: document.getElementById('scrollHours'), max: 23, key: 'h' },
      { el: document.getElementById('scrollMinutes'), max: 59, key: 'm' },
      { el: document.getElementById('scrollSeconds'), max: 59, key: 's' }
    ];

    scrollDefs.forEach(({ el, max, key }) => {
      const track = el.querySelector('.time-scroll__track');
      let items = [];
      for (let i = 0; i <= max; i++) {
        const item = document.createElement('div');
        item.className = 'time-scroll-item';
        item.textContent = String(i).padStart(2, '0');
        item.dataset.val = i;
        items.push(item);
        track.appendChild(item);
      }

      let selectedVal = 0;
      const updateSelected = (val) => {
        selectedVal = Math.max(0, Math.min(max, val));
        this.countdown[key] = selectedVal;
        items.forEach(item => {
          item.classList.toggle('selected', parseInt(item.dataset.val) === selectedVal);
        });
        const selectedEl = items[selectedVal];
        if (selectedEl) selectedEl.scrollIntoView({ block: 'center', behavior: 'smooth' });
      };

      updateSelected(0);

      el.addEventListener('wheel', e => {
        e.preventDefault();
        updateSelected(selectedVal + (e.deltaY > 0 ? 1 : -1));
      }, { passive: false });

      let startY = 0;
      el.addEventListener('touchstart', e => { startY = e.touches[0].clientY; });
      el.addEventListener('touchmove', e => {
        const dy = startY - e.touches[0].clientY;
        if (Math.abs(dy) > 20) {
          updateSelected(selectedVal + (dy > 0 ? 1 : -1));
          startY = e.touches[0].clientY;
        }
      });
    });
  },

  renderScrolls() {},

  startCountdown(total) {
    this.countdown.remaining = total;
    this.countdown.running = true;
    document.getElementById('atlantisAction').textContent = 'Пауза';
    document.getElementById('atlantisTimer').classList.add('running');

    const tsunami = document.querySelector('#atlantisTimer .atlantis-tsunami');
    if (tsunami) {
      tsunami.style.animationDuration = `2s, ${total}s`;
      tsunami.style.animationPlayState = 'running, running';
    }

    this.countdown.interval = setInterval(() => {
      this.countdown.remaining--;
      this.renderCountdownDisplay();
      if (this.countdown.remaining <= 0) {
        clearInterval(this.countdown.interval);
        this.countdown.running = false;
        document.getElementById('atlantisAction').textContent = 'Запустить';
        document.getElementById('atlantisTimer').classList.remove('running');
        if (tsunami) { tsunami.style.animationDuration = ''; tsunami.style.animationPlayState = ''; }
        this.playAlarmSound();
        alert('Время вышло! ⚡');
      }
    }, 1000);

    this.renderCountdownDisplay();
  },

  pauseCountdown() {
    clearInterval(this.countdown.interval);
    this.countdown.running = false;
    document.getElementById('atlantisAction').textContent = 'Запустить';
    const tsunami = document.querySelector('#atlantisTimer .atlantis-tsunami');
    if (tsunami) tsunami.style.animationPlayState = 'running, paused';
  },

  renderCountdownDisplay() {
    const r = this.countdown.remaining;
    const h = Math.floor(r / 3600);
    const m = Math.floor((r % 3600) / 60);
    const s = r % 60;
    document.getElementById('atlantisTimeDisplay').textContent =
      `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  },

  playAlarmSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [0, 0.3, 0.6].forEach(delay => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = 880;
        gain.gain.setValueAtTime(0.5, ctx.currentTime + delay);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + 0.4);
        osc.start(ctx.currentTime + delay);
        osc.stop(ctx.currentTime + delay + 0.4);
      });
    } catch {}
  },

  /* ===== Alarm ===== */
  initAlarm() {
    this.alarms = Storage.get('alarms', []);
    const addAlarmBtn = document.getElementById('addAlarmBtn');
    addAlarmBtn.addEventListener('click', () => this.addAlarm());
    addAlarmBtn.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this.addAlarm(); } });
  },

  addAlarm() {
    const time = prompt('Время будильника (ЧЧ:ММ):');
    if (!time || !/^\d{2}:\d{2}$/.test(time)) return;
    const name = prompt('Название:') || 'Будильник';
    const alarm = { id: Date.now(), time, name, active: true };
    this.alarms.push(alarm);
    Storage.set('alarms', this.alarms);
    this.renderAlarms();
    this.scheduleAlarm(alarm);
  },

  renderAlarms() {
    const container = document.getElementById('alarmArrows');
    container.innerHTML = '';
    const now = new Date();
    this.alarms.forEach(alarm => {
      const [h, m] = alarm.time.split(':').map(Number);
      const target = new Date();
      target.setHours(h, m, 0, 0);
      if (target <= now) target.setDate(target.getDate() + 1);
      const totalMs = target - now;
      const dayMs = 24 * 3600 * 1000;
      const progress = 1 - (totalMs / dayMs);

      const arrow = document.createElement('div');
      arrow.className = 'alarm-arrow';
      arrow.style.cssText = `left: ${Math.min(80, progress * 100)}%; bottom: ${20 + progress * 30}%;`;
      arrow.innerHTML = `
        <div class="alarm-arrow__shaft"></div>
        <div class="alarm-arrow__info">${alarm.time} — ${alarm.name}</div>
      `;
      arrow.title = 'Двойной клик — удалить';
      arrow.addEventListener('dblclick', () => {
        this.alarms = this.alarms.filter(a => a.id !== alarm.id);
        Storage.set('alarms', this.alarms);
        this.renderAlarms();
      });
      container.appendChild(arrow);
    });
  },

  scheduleAlarm(alarm) {
    const [h, m] = alarm.time.split(':').map(Number);
    const now = new Date();
    const target = new Date();
    target.setHours(h, m, 0, 0);
    if (target <= now) target.setDate(target.getDate() + 1);
    const delay = target - now;
    setTimeout(() => {
      this.playAlarmSound();
      alert(`⏰ Будильник: ${alarm.name}`);
    }, delay);
  },

  /* ===== Calendar ===== */
  initCalendar() {
    this.events = Storage.get('calendarEvents', {});
    document.getElementById('calPrevYear').addEventListener('click', () => {
      this.calYear--;
      document.getElementById('calYear').textContent = this.calYear;
      this.calMonth = null;
      this.renderCalendarMonths();
    });
    document.getElementById('calNextYear').addEventListener('click', () => {
      this.calYear++;
      document.getElementById('calYear').textContent = this.calYear;
      this.calMonth = null;
      this.renderCalendarMonths();
    });
  },

  renderCalendarMonths() {
    const months = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
    const container = document.getElementById('calMonths');
    const daysContainer = document.getElementById('calDays');
    container.innerHTML = '';
    daysContainer.classList.add('hidden');

    months.forEach((name, idx) => {
      const key = `${this.calYear}-${idx}`;
      const hasEvents = this.events[key] && Object.values(this.events[key]).some(d => d.length > 0);

      const pier = document.createElement('div');
      pier.className = 'cal-month-pier' + (hasEvents ? ' has-events' : '');
      pier.innerHTML = `⚓ ${name}`;
      pier.addEventListener('click', () => {
        this.calMonth = idx;
        this.renderCalendarDays(idx);
      });
      container.appendChild(pier);
    });
  },

  renderCalendarDays(monthIdx) {
    const months = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
    const container = document.getElementById('calDays');
    container.innerHTML = '';
    container.classList.remove('hidden');

    const year = this.calYear;
    const daysInMonth = new Date(year, monthIdx + 1, 0).getDate();
    const monthKey = `${year}-${monthIdx}`;

    for (let d = 1; d <= daysInMonth; d++) {
      const dayKey = `${monthKey}-${d}`;
      const dayEvents = (this.events[monthKey] && this.events[monthKey][d]) || [];

      const dayEl = document.createElement('div');
      dayEl.className = 'cal-day' + (dayEvents.length ? ' has-events' : '');
      dayEl.innerHTML = `<div class="cal-day__num">${d}</div>`;

      dayEvents.slice(0, 2).forEach(ev => {
        const evEl = document.createElement('div');
        evEl.className = 'cal-day__event';
        evEl.textContent = ev.name;
        dayEl.appendChild(evEl);
      });

      dayEl.addEventListener('click', () => {
        const name = prompt(`Событие ${d} ${months[monthIdx]}:`);
        if (!name) return;
        if (!this.events[monthKey]) this.events[monthKey] = {};
        if (!this.events[monthKey][d]) this.events[monthKey][d] = [];
        this.events[monthKey][d].push({ name, priority: 'bronze' });
        Storage.set('calendarEvents', this.events);
        this.renderCalendarDays(monthIdx);
      });

      container.appendChild(dayEl);
    }
  }
};

/* ===== Weather Section ===== */

const Weather = {
  days: ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'],
  months: ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек'],

  mockData: [
    { icon:'☀️', max:22, min:12, precip:5 },
    { icon:'⛅', max:19, min:10, precip:20 },
    { icon:'🌧️', max:15, min:8,  precip:80 },
    { icon:'🌦️', max:17, min:9,  precip:40 },
    { icon:'⛅', max:20, min:11, precip:15 },
    { icon:'☀️', max:24, min:13, precip:5  },
    { icon:'🌤️', max:21, min:12, precip:10 },
  ],

  init() {
    this.renderWeek();
    this.renderStats();
    this.setupFilters();
    document.getElementById('changeLocationBtn').addEventListener('click', () => {
      const city = prompt('Введите город:');
      if (city) document.getElementById('weatherLocationLabel').textContent = `📍 ${city}`;
    });
  },

  renderWeek() {
    const container = document.getElementById('weatherWeek');
    container.innerHTML = '';
    const today = new Date();

    this.mockData.forEach((d, i) => {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      const dayName = i === 0 ? 'Сегодня' : this.days[date.getDay()];

      const card = document.createElement('div');
      card.className = 'weather-day-card' + (i === 0 ? ' today' : '');
      card.innerHTML = `
        <div class="weather-day-name">${dayName}</div>
        <div class="weather-day-name" style="opacity:0.6;font-size:0.68rem;">${date.getDate()} ${this.months[date.getMonth()]}</div>
        <div class="weather-day-icon">${d.icon}</div>
        <div class="weather-day-temp">
          <span class="weather-temp-max">+${d.max}°</span>
          <span class="weather-temp-min">+${d.min}°</span>
        </div>
        <div class="weather-precip">💧 ${d.precip}%</div>
      `;
      container.appendChild(card);
    });
  },

  renderStats() {
    // Using mock values — in a real app, fetch from OpenMeteo
    document.getElementById('weatherWind').textContent = '14 км/ч';
    document.getElementById('weatherUV').textContent = '4 (Умеренный)';
    document.getElementById('weatherAir').textContent = 'Хорошее (AQI 42)';
    document.getElementById('weatherPressure').textContent = '758 мм рт. ст.';
    document.getElementById('weatherPressureDesc').textContent = 'Обычное · Падает';
  },

  setupFilters() {
    document.querySelectorAll('.weather-filter').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.weather-filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }
};

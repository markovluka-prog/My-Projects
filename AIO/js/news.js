/* ===== News Section ===== */

const NewsModule = {
  papers: {
    world: {
      title: '🌍 МИР',
      filters: [
        { key: 'politics', label: '🗺️ Политика' },
        { key: 'nature',   label: '🌿 Природа' },
        { key: 'society',  label: '🏙️ Общество' }
      ],
      headlines: [
        { title: 'Мировые лидеры обсудили климатические изменения', date: 'Сегодня', source: 'BBC', cat: 'nature' },
        { title: 'ООН призвала к диалогу в зонах конфликтов', date: 'Вчера', source: 'Reuters', cat: 'politics' },
        { title: 'В Европе растёт популярность возобновляемой энергии', date: '2 дня назад', source: 'DW', cat: 'nature' },
        { title: 'Города мира внедряют системы умного транспорта', date: 'Сегодня', source: 'CNN', cat: 'society' },
        { title: 'Переговоры по торговле продолжаются в Женеве', date: 'Вчера', source: 'Reuters', cat: 'politics' },
      ]
    },
    science: {
      title: '🔬 НАУКА',
      filters: [
        { key: 'bio',     label: '🧬 Биология' },
        { key: 'space',   label: '🚀 Космос' },
        { key: 'physics', label: '⚛️ Физика' }
      ],
      headlines: [
        { title: 'Учёные открыли новый вид антибиотиков из морских бактерий', date: 'Сегодня', source: 'N+1', cat: 'bio' },
        { title: 'NASA опубликовало снимки кольца Сатурна в высоком разрешении', date: 'Вчера', source: 'Nat. Geo', cat: 'space' },
        { title: 'Квантовый компьютер IBM установил рекорд вычислений', date: '3 дня назад', source: 'N+1', cat: 'physics' },
        { title: 'Мозг мыши полностью картирован — учёные раскрыли 84 000 нейронов', date: 'Сегодня', source: 'Nature', cat: 'bio' },
        { title: 'Марсоход Perseverance нашёл следы древней воды', date: 'Вчера', source: 'NASA', cat: 'space' },
      ]
    },
    tech: {
      title: '💻 ТЕХНОЛОГИИ',
      filters: [
        { key: 'ai',      label: '🤖 ИИ' },
        { key: 'gadgets', label: '📱 Гаджеты' },
        { key: 'games',   label: '🎮 Игры' }
      ],
      headlines: [
        { title: 'OpenAI представила новую модель с улучшенным рассуждением', date: 'Сегодня', source: 'Habr', cat: 'ai' },
        { title: 'Apple выпустила обновление с функцией 3D-сканирования', date: 'Вчера', source: 'The Verge', cat: 'gadgets' },
        { title: 'Steam установил рекорд — 40 миллионов пользователей онлайн', date: '2 дня назад', source: 'IGN', cat: 'games' },
        { title: 'Google DeepMind обучил ИИ предсказывать структуру белков', date: 'Сегодня', source: 'Habr', cat: 'ai' },
        { title: 'Xiaomi анонсировала складной телефон нового поколения', date: 'Вчера', source: 'GSMArena', cat: 'gadgets' },
      ]
    }
  },

  currentPaper: null,
  currentFilter: null,

  init() {
    const dateEl = document.getElementById('newsDateDisplay');
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });

    const facts = [
      'Учёные доказали, что растения общаются через грибковые сети в почве.',
      'Новый рекорд: первая в мире ферма на воде способна кормить 10 тысяч человек.',
      'Квантовый интернет прошёл первые испытания в Европе.',
      'ИИ впервые превзошёл человека в разработке новых лекарств.',
    ];
    document.getElementById('newsFactText').textContent = facts[Math.floor(Math.random() * facts.length)];

    document.querySelectorAll('.news-newspaper').forEach(el => {
      el.addEventListener('click', () => this.openPaper(el.dataset.paper));
    });

    document.getElementById('newsClosePaper').addEventListener('click', () => this.closePaper());
  },

  openPaper(paperKey) {
    this.currentPaper = paperKey;
    this.currentFilter = null;
    const paper = this.papers[paperKey];

    document.getElementById('newsKiosk').classList.add('hidden');
    document.getElementById('newsFactCard').classList.add('hidden');
    const openPaper = document.getElementById('newsOpenPaper');
    openPaper.classList.remove('hidden');

    document.getElementById('newsPaperHeader').textContent = paper.title;

    const filtersEl = document.getElementById('newsFilters');
    filtersEl.innerHTML = '';
    paper.filters.forEach(f => {
      const btn = document.createElement('button');
      btn.className = 'news-filter-btn';
      btn.textContent = f.label;
      btn.dataset.key = f.key;
      btn.addEventListener('click', () => {
        this.currentFilter = this.currentFilter === f.key ? null : f.key;
        filtersEl.querySelectorAll('.news-filter-btn').forEach(b => b.classList.remove('active'));
        if (this.currentFilter) btn.classList.add('active');
        this.renderHeadlines(paper);
      });
      filtersEl.appendChild(btn);
    });

    this.renderHeadlines(paper);
  },

  renderHeadlines(paper) {
    const container = document.getElementById('newsHeadlines');
    container.innerHTML = '';
    const filtered = this.currentFilter
      ? paper.headlines.filter(h => h.cat === this.currentFilter)
      : paper.headlines;

    filtered.forEach(h => {
      const el = document.createElement('div');
      el.className = 'news-headline';
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.innerHTML = `
        <div class="news-headline__title">${h.title}</div>
        <div class="news-headline__meta">
          <span class="news-headline__source-logo">${h.source}</span>
          ${h.date}
        </div>
      `;
      const openHeadline = () => {
        alert(`Открытие статьи: "${h.title}"\nИсточник: ${h.source}\n\n(В реальном приложении здесь откроется мини-браузер)`);
      };
      el.addEventListener('click', openHeadline);
      el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openHeadline(); } });
      container.appendChild(el);
    });
  },

  closePaper() {
    document.getElementById('newsOpenPaper').classList.add('hidden');
    document.getElementById('newsKiosk').classList.remove('hidden');
    document.getElementById('newsFactCard').classList.remove('hidden');
    this.currentPaper = null;
  }
};

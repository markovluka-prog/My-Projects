/* ===== AIO Main App ===== */

const App = {
  currentSection: 'home',

  init() {
    this.setupNavigation();
    this.loadUserState();
    this.initAIGuide();
  },

  setupNavigation() {
    // Sidebar nav buttons
    document.querySelectorAll('[data-section]').forEach(btn => {
      btn.addEventListener('click', () => {
        const section = btn.dataset.section;
        this.navigateTo(section);
      });
    });

    // Back buttons
    document.querySelectorAll('.back-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.navigateTo(btn.dataset.section || 'home');
      });
    });
  },

  navigateTo(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => {
      s.classList.add('hidden');
      s.classList.remove('active');
    });

    // Show target section
    const target = document.getElementById('section-' + sectionId);
    if (target) {
      target.classList.remove('hidden');
      target.classList.add('active');
    }

    // Update active nav button
    document.querySelectorAll('.sidebar__nav-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.section === sectionId);
    });

    this.currentSection = sectionId;

    // On mobile, close sidebar when navigating
    if (window.innerWidth <= 768) {
      Sidebar.close();
    }
  },

  loadUserState() {
    const user = Storage.get('user', { name: 'Гость', age: null, emoji: '👤' });
    document.getElementById('userName').textContent = user.name;
    document.getElementById('userAvatar').textContent = user.emoji;
    document.getElementById('userAgeLabel').textContent = user.age ? `${user.age} лет` : 'Укажите возраст';
  },

  initAIGuide() {
    const input = document.getElementById('aiInput');
    const sendBtn = document.getElementById('aiSendBtn');
    const voiceBtn = document.getElementById('aiVoiceBtn');

    const handleSend = () => {
      const text = input.value.trim();
      if (!text) return;
      this.addAIMessage(text, 'user');
      input.value = '';
      setTimeout(() => this.respondAI(text), 500);
    };

    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keydown', e => { if (e.key === 'Enter') handleSend(); });

    voiceBtn.addEventListener('click', () => {
      if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        this.addAIMessage('Голосовой ввод не поддерживается в этом браузере.', 'bot');
        return;
      }
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      const rec = new SR();
      rec.lang = 'ru-RU';
      rec.onresult = e => {
        input.value = e.results[0][0].transcript;
        handleSend();
      };
      rec.start();
    });
  },

  addAIMessage(text, type) {
    const chat = document.getElementById('aiChat');
    const msg = document.createElement('div');
    msg.className = `ai-message ai-message--${type}`;
    msg.textContent = text;
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
  },

  respondAI(query) {
    const q = query.toLowerCase();
    const routes = [
      { keys: ['запис', 'заметк', 'блокнот', 'книг', 'список'], section: 'notes', label: 'Записи' },
      { keys: ['таймер', 'время', 'будильник', 'календарь', 'событи'], section: 'timer', label: 'Тайм-менеджер' },
      { keys: ['погод', 'дождь', 'температур', 'ветер', 'снег'], section: 'weather', label: 'Погода' },
      { keys: ['фильм', 'кино', 'смотрет', 'сериал'], section: 'movies', label: 'Фильмы' },
      { keys: ['новост', 'газет', 'новость', 'наука', 'технолог', 'мир'], section: 'news', label: 'Новости' },
      { keys: ['игр', 'поиграт', 'аркад', 'головоломк', 'стратег'], section: 'games', label: 'Игры' },
      { keys: ['финанс', 'деньг', 'трат', 'бюджет', 'расход', 'доход'], section: 'finance', label: 'Финансы' },
      { keys: ['перевод', 'язык', 'переводч', 'английск', 'вавилон'], section: 'translator', label: 'Переводчик' },
      { keys: ['калькулят', 'счёт', 'посчита', 'математик', 'число'], section: 'calc', label: 'Калькулятор' },
      { keys: ['семь', 'семья', 'родител', 'ребёнок', 'детей', 'покупк'], section: 'family', label: 'Семья' },
      { keys: ['рецепт', 'готовит', 'блюдо', 'еда', 'приготов', 'кулинар'], section: 'recipes', label: 'Рецепты' },
      { keys: ['привычк', 'трекер', 'сад', 'здоровь', 'спорт', 'медитац'], section: 'habits', label: 'Привычки' },
      { keys: ['документ', 'скан', 'pdf', 'подпис', 'бумаг'], section: 'documents', label: 'Документы' },
      { keys: ['музык', 'песн', 'трек', 'слушат', 'концерт'], section: 'music', label: 'Музыка' },
    ];

    const match = routes.find(r => r.keys.some(k => q.includes(k)));

    if (match) {
      this.addAIMessage(`Нашёл! Открываю раздел «${match.label}» ✨`, 'bot');
      setTimeout(() => this.navigateTo(match.section), 600);
    } else if (q.includes('главн') || q.includes('меню') || q.includes('домой')) {
      this.addAIMessage('Возвращаемся на главную!', 'bot');
      setTimeout(() => this.navigateTo('home'), 400);
    } else {
      this.addAIMessage(`Не нашёл точного совпадения для «${query}». Попробуйте: "фильмы", "погода", "калькулятор" и т.д.`, 'bot');
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();

  // Initialize all section modules
  if (typeof Notes !== 'undefined') Notes.init();
  if (typeof TimerModule !== 'undefined') TimerModule.init();
  if (typeof Weather !== 'undefined') Weather.init();
  if (typeof Movies !== 'undefined') Movies.init();
  if (typeof NewsModule !== 'undefined') NewsModule.init();
  if (typeof Games !== 'undefined') Games.init();
  if (typeof Finance !== 'undefined') Finance.init();
  if (typeof Translator !== 'undefined') Translator.init();
  if (typeof Calc !== 'undefined') Calc.init();
  if (typeof Family !== 'undefined') Family.init();
  if (typeof Recipes !== 'undefined') Recipes.init();
  if (typeof Habits !== 'undefined') Habits.init();
  if (typeof Documents !== 'undefined') Documents.init();
  if (typeof Music !== 'undefined') Music.init();
});

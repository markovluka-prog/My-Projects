/* ===== Translator Section ===== */

const Translator = {
  fromLang: 'ru',
  toLang: 'en',
  pickingFor: null,

  languages: [
    { code: 'ru', name: 'Русский', tier: 1 },
    { code: 'en', name: 'Английский', tier: 1 },
    { code: 'zh', name: 'Китайский', tier: 1 },
    { code: 'es', name: 'Испанский', tier: 2 },
    { code: 'fr', name: 'Французский', tier: 2 },
    { code: 'de', name: 'Немецкий', tier: 2 },
    { code: 'ja', name: 'Японский', tier: 3 },
    { code: 'ar', name: 'Арабский', tier: 3 },
    { code: 'pt', name: 'Португальский', tier: 4 },
    { code: 'it', name: 'Итальянский', tier: 4 },
    { code: 'ko', name: 'Корейский', tier: 5 },
    { code: 'hi', name: 'Хинди', tier: 5 },
    { code: 'tr', name: 'Турецкий', tier: 6 },
    { code: 'pl', name: 'Польский', tier: 6 },
    { code: 'nl', name: 'Нидерландский', tier: 7 },
    { code: 'sv', name: 'Шведский', tier: 7 },
    { code: 'uk', name: 'Украинский', tier: 8 },
  ],

  init() {
    this.renderTower();
    this.updateLabels();

    document.getElementById('translateBtn').addEventListener('click', () => this.translate());
    document.getElementById('swapLangsBtn').addEventListener('click', () => {
      [this.fromLang, this.toLang] = [this.toLang, this.fromLang];
      this.updateLabels();
    });

    document.getElementById('fromLangBtn').addEventListener('click', () => this.openLangPicker('from'));
    document.getElementById('toLangBtn').addEventListener('click', () => this.openLangPicker('to'));
    document.getElementById('langModalClose').addEventListener('click', () => {
      document.getElementById('langModal').classList.add('hidden');
    });

    document.getElementById('voiceTranslateBtn').addEventListener('click', () => this.voiceInput());

    document.getElementById('translateInput').addEventListener('keydown', e => {
      if (e.ctrlKey && e.key === 'Enter') this.translate();
    });
  },

  renderTower() {
    const tower = document.getElementById('babelTower');
    const tiers = {};
    this.languages.forEach(l => {
      if (!tiers[l.tier]) tiers[l.tier] = [];
      tiers[l.tier].push(l);
    });

    const maxTier = Math.max(...Object.keys(tiers).map(Number));
    for (let t = 1; t <= maxTier; t++) {
      const langs = tiers[t] || [];
      const tierEl = document.createElement('div');
      tierEl.className = 'babel-tier';
      const width = 100 - (t - 1) * 8;
      tierEl.style.cssText = `width:${width}%;font-size:${0.78 - (t-1)*0.02}rem;`;
      tierEl.innerHTML = langs.map(l => l.name).join(', ');
      tower.appendChild(tierEl);
    }
  },

  updateLabels() {
    const from = this.languages.find(l => l.code === this.fromLang);
    const to = this.languages.find(l => l.code === this.toLang);
    document.getElementById('fromLangLabel').textContent = from ? from.name : this.fromLang;
    document.getElementById('toLangLabel').textContent = to ? to.name : this.toLang;
  },

  openLangPicker(which) {
    this.pickingFor = which;
    document.getElementById('langModalTitle').textContent = which === 'from' ? 'Язык оригинала' : 'Язык перевода';

    const list = document.getElementById('langList');
    list.innerHTML = '';
    this.languages.forEach(l => {
      const btn = document.createElement('button');
      btn.className = 'lang-option' + ((which === 'from' ? this.fromLang : this.toLang) === l.code ? ' active' : '');
      btn.textContent = l.name;
      btn.addEventListener('click', () => {
        if (which === 'from') this.fromLang = l.code;
        else this.toLang = l.code;
        this.updateLabels();
        document.getElementById('langModal').classList.add('hidden');
      });
      list.appendChild(btn);
    });

    document.getElementById('langModal').classList.remove('hidden');
  },

  async translate() {
    const text = document.getElementById('translateInput').value.trim();
    if (!text) return;

    const output = document.getElementById('translateOutput');
    output.textContent = '⏳ Переводим...';

    try {
      const res = await fetch(`https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${this.fromLang}|${this.toLang}`);
      const data = await res.json();
      output.textContent = data.responseData?.translatedText || 'Не удалось перевести';
    } catch {
      // Fallback: show mock translation
      output.textContent = `[${this.toLang}] ${text}`;
    }
  },

  voiceInput() {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Голосовой ввод не поддерживается в этом браузере.');
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    const langMap = { ru: 'ru-RU', en: 'en-US', de: 'de-DE', fr: 'fr-FR', es: 'es-ES', zh: 'zh-CN', ja: 'ja-JP' };
    rec.lang = langMap[this.fromLang] || 'ru-RU';
    rec.onresult = e => {
      document.getElementById('translateInput').value = e.results[0][0].transcript;
      this.translate();
    };
    rec.onerror = () => alert('Ошибка распознавания речи.');
    rec.start();
  }
};

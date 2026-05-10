/* ===== Movies Section ===== */

const Movies = {
  recommendations: [
    { emoji:'🚀', title:'Интерстеллар', year:2014 },
    { emoji:'🦁', title:'Король Лев', year:2019 },
    { emoji:'🕷️', title:'Человек-паук', year:2002 },
    { emoji:'🧙', title:'Гарри Поттер', year:2001 },
    { emoji:'🤖', title:'ВАЛЛ·И', year:2008 },
    { emoji:'🐉', title:'Как приручить дракона', year:2010 },
    { emoji:'🌊', title:'Моана', year:2016 },
    { emoji:'🦸', title:'Мстители', year:2012 },
  ],

  init() {
    this.renderPortholes(document.getElementById('moviesPortholes'), this.recommendations);

    const searchInput = document.getElementById('moviesSearch');
    const resultsEl = document.getElementById('moviesResults');

    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim().toLowerCase();
      if (!q) {
        resultsEl.classList.add('hidden');
        return;
      }
      const results = this.recommendations.filter(m => m.title.toLowerCase().includes(q));
      if (results.length) {
        resultsEl.classList.remove('hidden');
        this.renderPortholes(resultsEl, results);
      } else {
        resultsEl.innerHTML = '<p style="color:rgba(232,201,122,0.5);padding:12px;">Ничего не найдено</p>';
        resultsEl.classList.remove('hidden');
      }
    });
  },

  renderPortholes(container, movies) {
    container.innerHTML = '';
    movies.forEach(m => {
      const el = document.createElement('div');
      el.className = 'porthole';
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('aria-label', `${m.title} (${m.year})`);
      el.innerHTML = `
        <div class="porthole__frame">${m.emoji}</div>
        <div class="porthole__label">${m.title}<br/><span style="opacity:0.5;font-size:0.7rem;">${m.year}</span></div>
      `;
      const openMovie = () => this.showMovieInfo(m, container);
      el.addEventListener('click', openMovie);
      el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openMovie(); } });
      container.appendChild(el);
    });
  },

  showMovieInfo(movie, _) {
    const existing = document.querySelector('.movie-info-panel');
    if (existing) existing.remove();

    const panel = document.createElement('div');
    panel.className = 'movie-info-panel';
    panel.innerHTML = `
      <h3>${movie.emoji} ${movie.title} (${movie.year})</h3>
      <p>Один из лучших фильмов в своём жанре. Подходит для всей семьи.</p>
      <div style="display:flex;gap:10px;">
        <button class="movie-watch-btn" onclick="window.open('https://www.youtube.com/results?search_query=${encodeURIComponent(movie.title)}','_blank')">▶ Смотреть</button>
        <button onclick="this.closest('.movie-info-panel').remove()" style="padding:10px 16px;color:rgba(232,201,122,0.6);font-size:0.9rem;">Закрыть</button>
      </div>
    `;
    document.getElementById('section-movies').appendChild(panel);
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};

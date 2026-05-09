/* ===== Games Section ===== */

const Games = {
  tents: [
    {
      color: 'red', icon: '🕹️', label: 'Аркады',
      games: [
        { name: '🚀 Asteroids', url: 'https://www.crazygames.com/game/asteroids' },
        { name: '🐍 Змейка', url: 'https://www.crazygames.com/game/snake' },
        { name: '🏓 Пинг-понг', url: 'https://www.crazygames.com/game/ping-pong' },
      ]
    },
    {
      color: 'blue', icon: '🧩', label: 'Головоломки',
      games: [
        { name: '🔷 2048', url: 'https://www.crazygames.com/game/2048' },
        { name: '🎯 Судоку', url: 'https://www.crazygames.com/game/sudoku' },
        { name: '🟩 Wordle', url: 'https://www.nytimes.com/games/wordle' },
      ]
    },
    {
      color: 'green', icon: '⚔️', label: 'Стратегии',
      games: [
        { name: '🏰 Tower Defence', url: 'https://www.crazygames.com/game/tower-defense' },
        { name: '🌍 GeoGuessr Lite', url: 'https://www.geoguessr.com/' },
        { name: '♟️ Шахматы', url: 'https://www.chess.com/play/online' },
      ]
    },
    {
      color: 'yellow', icon: '🏎️', label: 'Гонки',
      games: [
        { name: '🚗 Madalin Cars', url: 'https://www.crazygames.com/game/madalin-cars' },
        { name: '🛵 Moto X3M', url: 'https://www.crazygames.com/game/moto-x3m' },
        { name: '🏁 Tron Bikes', url: 'https://www.crazygames.com/game/tron-bikes' },
      ]
    },
    {
      color: 'purple', icon: '🎲', label: 'Разное',
      games: [
        { name: '🃏 Пасьянс', url: 'https://www.crazygames.com/game/classic-solitaire' },
        { name: '🎳 Боулинг', url: 'https://www.crazygames.com/game/bowling' },
        { name: '🎮 Тетрис', url: 'https://tetris.com/play-tetris' },
      ]
    }
  ],

  init() {
    this.renderTents();

    document.getElementById('gamesSearch').addEventListener('input', e => {
      const q = e.target.value.trim().toLowerCase();
      if (!q) { this.renderTents(); return; }
      const filtered = this.tents.map(t => ({
        ...t,
        games: t.games.filter(g => g.name.toLowerCase().includes(q) || t.label.toLowerCase().includes(q))
      })).filter(t => t.games.length > 0);
      this.renderTents(filtered);
    });
  },

  renderTents(tents = this.tents) {
    const container = document.getElementById('gamesTents');
    container.innerHTML = '';
    tents.forEach(tent => {
      const el = document.createElement('div');
      el.className = `game-tent game-tent--${tent.color}`;
      el.innerHTML = `
        <div class="game-tent__roof"></div>
        <div class="game-tent__body">
          <div class="game-tent__icon">${tent.icon}</div>
          <div class="game-tent__label">${tent.label}</div>
          <div class="game-tent__games">
            ${tent.games.map(g => `<button class="game-tent__game" data-url="${g.url}">${g.name}</button>`).join('')}
          </div>
        </div>
      `;
      el.querySelectorAll('.game-tent__game').forEach(btn => {
        btn.addEventListener('click', e => {
          e.stopPropagation();
          window.open(btn.dataset.url, '_blank');
        });
      });
      container.appendChild(el);
    });
  }
};

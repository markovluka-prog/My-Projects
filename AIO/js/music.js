/* ===== Music Section ===== */

const Music = {
  currentTrack: null,
  playing: false,
  progress: 0,
  progressInterval: null,

  recommendations: [
    { icon: '🎸', title: 'Imagine Dragons', genre: 'Рок' },
    { icon: '🎹', title: 'Ludovico Einaudi', genre: 'Классика' },
    { icon: '🎤', title: 'Billie Eilish', genre: 'Поп' },
    { icon: '🎺', title: 'Louis Armstrong', genre: 'Джаз' },
    { icon: '🥁', title: 'Linkin Park', genre: 'Рок' },
    { icon: '🎻', title: 'Hans Zimmer', genre: 'Саундтрек' },
  ],

  mockTracks: [
    { icon: '🎵', title: 'Believer', artist: 'Imagine Dragons' },
    { icon: '🎵', title: 'Una Mattina', artist: 'Einaudi' },
    { icon: '🎵', title: 'Bad Guy', artist: 'Billie Eilish' },
    { icon: '🎵', title: 'Nuvole Bianche', artist: 'Einaudi' },
    { icon: '🎵', title: 'What I\'ve Done', artist: 'Linkin Park' },
    { icon: '🎵', title: 'Interstellar Theme', artist: 'Hans Zimmer' },
    { icon: '🎵', title: 'Thunderstruck', artist: 'AC/DC' },
    { icon: '🎵', title: 'Bohemian Rhapsody', artist: 'Queen' },
  ],

  init() {
    this.renderPosters();
    this.renderResults(this.mockTracks);

    document.getElementById('musicPlayPause').addEventListener('click', () => this.togglePlay());
    document.getElementById('musicPrev').addEventListener('click', () => this.prev());
    document.getElementById('musicNext').addEventListener('click', () => this.next());

    const search = document.getElementById('musicSearch');
    search.addEventListener('input', () => {
      const q = search.value.trim().toLowerCase();
      const filtered = q
        ? this.mockTracks.filter(t => t.title.toLowerCase().includes(q) || t.artist.toLowerCase().includes(q))
        : this.mockTracks;
      this.renderResults(filtered);
    });
  },

  renderPosters() {
    const container = document.getElementById('concertPosters');
    const label = document.createElement('div');
    label.className = 'concert-poster-label';
    label.textContent = 'Для вас';
    container.appendChild(label);

    this.recommendations.forEach(rec => {
      const poster = document.createElement('div');
      poster.className = 'concert-poster';
      poster.innerHTML = `
        <div class="concert-poster__icon">${rec.icon}</div>
        <div class="concert-poster__title">${rec.title}<br/><span style="opacity:0.5;font-size:0.65rem;">${rec.genre}</span></div>
      `;
      poster.addEventListener('click', () => {
        const track = this.mockTracks.find(t => t.artist.includes(rec.title.split(' ')[0])) || this.mockTracks[0];
        this.playTrack(track);
      });
      container.appendChild(poster);
    });
  },

  renderResults(tracks) {
    const container = document.getElementById('musicResults');
    container.innerHTML = '';
    tracks.forEach(track => {
      const ticket = document.createElement('div');
      ticket.className = 'music-ticket';
      ticket.innerHTML = `
        <div class="music-ticket__icon">${track.icon}</div>
        <div class="music-ticket__info">
          <div class="music-ticket__title">${track.title}</div>
          <div class="music-ticket__artist">${track.artist}</div>
        </div>
      `;
      ticket.addEventListener('click', () => this.playTrack(track));
      container.appendChild(ticket);
    });
  },

  playTrack(track) {
    this.currentTrack = track;
    this.playing = true;
    this.progress = 0;

    document.getElementById('stageTrackName').textContent = `${track.title} — ${track.artist}`;
    document.getElementById('stageArtist').textContent = '🎤';
    document.getElementById('musicPlayPause').textContent = '⏸';

    this.startProgress();
    const searchUrl = `https://music.youtube.com/search?q=${encodeURIComponent(track.title + ' ' + track.artist)}`;
    window.open(searchUrl, '_blank');
  },

  togglePlay() {
    if (!this.currentTrack) return;
    this.playing = !this.playing;
    document.getElementById('musicPlayPause').textContent = this.playing ? '⏸' : '▶';
    if (this.playing) this.startProgress();
    else clearInterval(this.progressInterval);
  },

  startProgress() {
    clearInterval(this.progressInterval);
    this.progressInterval = setInterval(() => {
      this.progress = Math.min(100, this.progress + 0.5);
      document.getElementById('stageCurtain').style.width = this.progress + '%';
      if (this.progress >= 100) {
        clearInterval(this.progressInterval);
        this.next();
      }
    }, 300);
  },

  prev() {
    if (!this.currentTrack) return;
    const idx = this.mockTracks.findIndex(t => t.title === this.currentTrack.title);
    const prev = this.mockTracks[(idx - 1 + this.mockTracks.length) % this.mockTracks.length];
    this.playTrack(prev);
  },

  next() {
    if (!this.currentTrack) return;
    const idx = this.mockTracks.findIndex(t => t.title === this.currentTrack.title);
    const next = this.mockTracks[(idx + 1) % this.mockTracks.length];
    this.playTrack(next);
  }
};

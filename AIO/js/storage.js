const Storage = {
  get(key, fallback = null) {
    try {
      const v = localStorage.getItem('aio_' + key);
      return v !== null ? JSON.parse(v) : fallback;
    } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem('aio_' + key, JSON.stringify(value)); } catch {}
  },
  remove(key) {
    try { localStorage.removeItem('aio_' + key); } catch {}
  }
};

/* ===== AIO Visual Effects ===== */

const VisualEffects = {
  starCanvas: null,
  ctx: null,
  stars: [],
  animFrame: null,

  init() {
    this.initStarfield();
    this.initCardGlows();
  },

  /* ===== Starfield on home page ===== */
  initStarfield() {
    const homeSection = document.getElementById('section-home');
    if (!homeSection) return;

    const canvas = document.createElement('canvas');
    canvas.id = 'starCanvas';
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:0;';
    homeSection.insertBefore(canvas, homeSection.firstChild);

    this.starCanvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.resizeCanvas();
    this.generateStars(160);
    this.animateStars();

    window.addEventListener('resize', () => {
      this.resizeCanvas();
      this.generateStars(160);
    });
  },

  resizeCanvas() {
    if (!this.starCanvas) return;
    this.starCanvas.width = this.starCanvas.offsetWidth;
    this.starCanvas.height = this.starCanvas.offsetHeight;
  },

  generateStars(count) {
    const w = this.starCanvas.width;
    const h = this.starCanvas.height;
    this.stars = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 1.5 + 0.3,
      opacity: Math.random(),
      speed: Math.random() * 0.008 + 0.003,
      phase: Math.random() * Math.PI * 2,
    }));
  },

  animateStars() {
    const ctx = this.ctx;
    const canvas = this.starCanvas;
    const draw = (t) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      this.stars.forEach(s => {
        const o = 0.2 + 0.8 * (0.5 + 0.5 * Math.sin(t * s.speed + s.phase));
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${o})`;
        ctx.fill();
      });
      this.animFrame = requestAnimationFrame(draw);
    };
    this.animFrame = requestAnimationFrame(draw);
  },

  stopStarfield() {
    if (this.animFrame) cancelAnimationFrame(this.animFrame);
  },

  /* ===== Per-section card glow colors ===== */
  initCardGlows() {
    const glowMap = {
      notes:      '58,125,68',
      timer:      '37,99,235',
      weather:    '78,181,230',
      movies:     '10,61,98',
      news:       '139,105,20',
      games:      '231,76,60',
      finance:    '212,160,23',
      translator: '139,69,19',
      calc:       '230,126,34',
      family:     '139,105,20',
      recipes:    '58,125,68',
      habits:     '46,204,113',
      documents:  '44,95,138',
      music:      '107,28,46',
    };

    document.querySelectorAll('.home-card').forEach(card => {
      const section = card.dataset.section;
      const rgb = glowMap[section];
      if (!rgb) return;
      card.addEventListener('mouseenter', () => {
        card.style.boxShadow = `0 8px 32px rgba(${rgb},0.45), 0 0 0 1px rgba(${rgb},0.3)`;
      });
      card.addEventListener('mouseleave', () => {
        card.style.boxShadow = '';
      });
    });
  },

  /* ===== Ripple effect on button click ===== */
  addRipple(el) {
    el.addEventListener('click', function(e) {
      const rect = el.getBoundingClientRect();
      const ripple = document.createElement('span');
      ripple.style.cssText = `
        position:absolute;border-radius:50%;background:rgba(255,255,255,0.3);
        width:60px;height:60px;margin:-30px;
        left:${e.clientX - rect.left}px;top:${e.clientY - rect.top}px;
        animation:ripple 0.6s ease-out forwards;pointer-events:none;
      `;
      el.style.position = 'relative';
      el.style.overflow = 'hidden';
      el.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  },
};

document.addEventListener('DOMContentLoaded', () => VisualEffects.init());

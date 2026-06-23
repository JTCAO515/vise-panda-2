/* ============================================
   ViseBits - React Bits Components for VisePanda
   Vanilla JS adaptation
   ============================================ */

(function() {
  'use strict';

  /* ──────────────────────────────────────────
     1. Aurora / Beams Hero Background
     ────────────────────────────────────────── */
  class AuroraHero {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.beams = [];
      this.time = 0;
      this.resize();
      this.initBeams();
      window.addEventListener('resize', () => this.resize());
      this.animate();
    }

    resize() {
      const rect = this.canvas.parentElement.getBoundingClientRect();
      this.canvas.width = rect.width * devicePixelRatio;
      this.canvas.height = rect.height * devicePixelRatio;
      this.ctx.scale(devicePixelRatio, devicePixelRatio);
      this.w = rect.width;
      this.h = rect.height;
    }

    initBeams() {
      this.beams = [];
      const count = 8 + Math.floor(this.w / 200);
      for (let i = 0; i < count; i++) {
        this.beams.push({
          x: Math.random() * this.w,
          y: this.h * (0.2 + Math.random() * 0.6),
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.3,
          width: 30 + Math.random() * 80,
          speed: 0.3 + Math.random() * 0.7,
          opacity: 0.03 + Math.random() * 0.08,
          hue: 200 + Math.random() * 40,  // blue-teal range
          sat: 60 + Math.random() * 30,
          phase: Math.random() * Math.PI * 2,
        });
      }
    }

    animate() {
      this.time += 0.008;
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.w, this.h);

      // Draw aurora layers
      for (const b of this.beams) {
        const x = b.x + Math.sin(this.time * b.speed + b.phase) * 60;
        const y = b.y + Math.cos(this.time * b.speed * 0.7 + b.phase) * 40;
        const w = b.width + Math.sin(this.time * 0.3 + b.phase) * 20;

        const gradient = ctx.createRadialGradient(x, y, 0, x, y, w);
        gradient.addColorStop(0, `hsla(${b.hue}, ${b.sat}%, 60%, ${b.opacity * 2})`);
        gradient.addColorStop(0.4, `hsla(${b.hue + 10}, ${b.sat - 10}%, 55%, ${b.opacity})`);
        gradient.addColorStop(1, `hsla(${b.hue + 20}, ${b.sat}%, 50%, 0)`);

        ctx.beginPath();
        ctx.fillStyle = gradient;
        ctx.ellipse(x, y, w, w * 0.3, Math.sin(this.time * 0.1 + b.phase) * 0.5, 0, Math.PI * 2);
        ctx.fill();

        // Light rays (beams)
        const rayCount = 5 + Math.floor(Math.random() * 3);
        for (let r = 0; r < rayCount; r++) {
          const angle = (r / rayCount) * Math.PI * 2 + this.time * 0.05 + b.phase;
          const len = w * 0.8 + Math.sin(this.time * 0.5 + r + b.phase) * w * 0.3;
          const endX = x + Math.cos(angle) * len;
          const endY = y + Math.sin(angle) * len * 0.3;

          const rayGrad = ctx.createLinearGradient(x, y, endX, endY);
          rayGrad.addColorStop(0, `hsla(${b.hue + 15}, ${b.sat}%, 65%, ${b.opacity * 0.5})`);
          rayGrad.addColorStop(1, 'hsla(0, 0%, 100%, 0)');

          ctx.beginPath();
          ctx.strokeStyle = rayGrad;
          ctx.lineWidth = 1 + Math.random();
          ctx.moveTo(x, y);
          ctx.lineTo(endX, endY);
          ctx.stroke();
        }

        b.x += b.vx;
        b.y += b.vy;
        if (b.x < -200) b.x = this.w + 100;
        if (b.x > this.w + 200) b.x = -100;
        if (b.y < -100) b.y = this.h + 100;
        if (b.y > this.h + 100) b.y = -100;
      }

      // Soft overlay glow
      const overlay = ctx.createRadialGradient(this.w / 2, this.h / 2, 0, this.w / 2, this.h / 2, this.w * 0.6);
      overlay.addColorStop(0, 'rgba(14, 165, 233, 0.02)');
      overlay.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = overlay;
      ctx.fillRect(0, 0, this.w, this.h);

      requestAnimationFrame(() => this.animate());
    }
  }

  /* ──────────────────────────────────────────
     2. Tilted Card (3D perspective on hover)
     ────────────────────────────────────────── */
  class TiltedCard {
    constructor(element, options = {}) {
      this.element = element;
      this.options = {
        maxTilt: options.maxTilt || 8,
        perspective: options.perspective || 1000,
        scale: options.scale || 1.02,
        speed: options.speed || 300,
        glare: options.glare !== false,
        ...options,
      };
      this.element.classList.add('vise-tilt');
      this.isMobile = window.matchMedia('(pointer: coarse)').matches;
      if (this.isMobile) return;

      // Create inner wrapper for content
      const inner = document.createElement('div');
      inner.className = 'vise-tilt-inner';
      while (this.element.firstChild) inner.appendChild(this.element.firstChild);
      this.element.appendChild(inner);
      this.inner = inner;

      // Glow effect
      if (this.options.glare) {
        this.glow = document.createElement('div');
        this.glow.className = 'vise-tilt-glow';
        this.element.appendChild(this.glow);
        this.shine = document.createElement('div');
        this.shine.className = 'vise-tilt-shine';
        this.element.appendChild(this.shine);
      }

      this.boundMove = this.onMouseMove.bind(this);
      this.boundLeave = this.onMouseLeave.bind(this);
      this.element.addEventListener('mousemove', this.boundMove);
      this.element.addEventListener('mouseleave', this.boundLeave);
    }

    onMouseMove(e) {
      const rect = this.element.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const rotateX = ((y - centerY) / centerY) * -this.options.maxTilt;
      const rotateY = ((x - centerX) / centerX) * this.options.maxTilt;

      this.element.style.transform = `
        perspective(${this.options.perspective}px)
        rotateX(${rotateX}deg)
        rotateY(${rotateY}deg)
        scale3d(${this.options.scale}, ${this.options.scale}, ${this.options.scale})
      `;

      // Track mouse for glow
      if (this.glow) {
        const pctX = (x / rect.width) * 100;
        const pctY = (y / rect.height) * 100;
        this.glow.style.setProperty('--mouse-x', pctX + '%');
        this.glow.style.setProperty('--mouse-y', pctY + '%');
      }
    }

    onMouseLeave() {
      this.element.style.transform = '';
      this.element.style.transition = `transform ${this.options.speed}ms ease`;
      setTimeout(() => { this.element.style.transition = ''; }, this.options.speed);
    }

    destroy() {
      this.element.removeEventListener('mousemove', this.boundMove);
      this.element.removeEventListener('mouseleave', this.boundLeave);
    }
  }

  /* ──────────────────────────────────────────
     3. Spotlight Card (radial glow on hover)
     ────────────────────────────────────────── */
  class SpotlightCard {
    constructor(element) {
      this.element = element;
      element.classList.add('vise-spotlight');
      this.isMobile = window.matchMedia('(pointer: coarse)').matches;
      if (this.isMobile) return;

      // Create border effect layer
      this.border = document.createElement('div');
      this.border.className = 'vise-spotlight-border';
      element.appendChild(this.border);

      this.boundMove = this.onMouseMove.bind(this);
      this.boundLeave = this.onMouseLeave.bind(this);
      this.element.addEventListener('mousemove', this.boundMove);
      this.element.addEventListener('mouseleave', this.boundLeave);
    }

    onMouseMove(e) {
      const rect = this.element.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      this.element.style.setProperty('--mouse-x', x + '%');
      this.element.style.setProperty('--mouse-y', y + '%');
    }

    onMouseLeave() {
      // Border fade stays smooth via CSS transition
    }

    destroy() {
      this.element.removeEventListener('mousemove', this.boundMove);
      this.element.removeEventListener('mouseleave', this.boundLeave);
    }
  }

  /* ──────────────────────────────────────────
     4. Count Up (animated number counter)
     ────────────────────────────────────────── */
  class CountUp {
    constructor(element, options = {}) {
      this.element = element;
      this.target = options.target || 0;
      this.duration = options.duration || 2000;
      this.decimals = options.decimals || 0;
      this.suffix = options.suffix || '';
      this.prefix = options.prefix || '';
      this.observed = false;
      this.animated = false;

      element.classList.add('vise-countup');

      const numSpan = document.createElement('span');
      numSpan.className = 'vise-countup-number';
      numSpan.textContent = '0';
      this.numSpan = numSpan;
      element.appendChild(numSpan);

      if (this.suffix) {
        const suffixSpan = document.createElement('span');
        suffixSpan.className = 'vise-countup-suffix';
        suffixSpan.textContent = this.suffix;
        element.appendChild(suffixSpan);
      }

      this.observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !this.animated) {
          this.animated = true;
          this.animate();
          this.observer.disconnect();
        }
      }, { threshold: 0.3 });
      this.observer.observe(element);
    }

    animate() {
      const start = performance.now();
      const from = 0;
      const to = this.target;

      const tick = (now) => {
        const elapsed = now - start;
        const progress = Math.min(elapsed / this.duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = from + (to - from) * eased;
        this.numSpan.textContent = this.prefix + value.toFixed(this.decimals);

        if (progress < 1) {
          requestAnimationFrame(tick);
        }
      };
      requestAnimationFrame(tick);
    }
  }

  /* ──────────────────────────────────────────
     5. Splash Cursor (click particle effect)
     ────────────────────────────────────────── */
  class SplashCursor {
    constructor(options = {}) {
      this.options = {
        colors: options.colors || [
          '#0ea5e9', '#f97316', '#2d8a63', '#8b5cf6',
          '#ec4899', '#fbbf24', '#14b8a6',
        ],
        particleCount: options.particleCount || 12,
        lifetime: options.lifetime || 800,
        size: options.size || 6,
        spread: options.spread || 100,
        gravity: options.gravity || 0.05,
        ...options,
      };
      this.setup();
    }

    setup() {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'vise-splash-canvas';
      document.body.appendChild(this.canvas);
      this.ctx = this.canvas.getContext('2d');
      this.particles = [];
      this.resize();

      window.addEventListener('resize', () => this.resize());
      document.addEventListener('click', (e) => this.splash(e.clientX, e.clientY));
      document.addEventListener('touchstart', (e) => {
        const touch = e.touches[0];
        if (touch) this.splash(touch.clientX, touch.clientY);
      }, { passive: true });

      this.animate();
    }

    resize() {
      this.canvas.width = window.innerWidth * devicePixelRatio;
      this.canvas.height = window.innerHeight * devicePixelRatio;
      this.ctx.scale(devicePixelRatio, devicePixelRatio);
      this.w = window.innerWidth;
      this.h = window.innerHeight;
    }

    splash(x, y) {
      const count = this.options.particleCount;
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2 + (Math.random() - 0.5) * 0.5;
        const speed = 2 + Math.random() * 4;
        this.particles.push({
          x, y,
          vx: Math.cos(angle) * speed * (0.5 + Math.random()),
          vy: Math.sin(angle) * speed * (0.5 + Math.random()),
          size: this.options.size * (0.4 + Math.random() * 0.6),
          color: this.options.colors[Math.floor(Math.random() * this.options.colors.length)],
          alpha: 1,
          decay: 0.015 + Math.random() * 0.02,
          gravity: this.options.gravity,
          born: Date.now(),
          lifetime: this.options.lifetime,
        });
      }
    }

    animate() {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.w, this.h);

      this.particles = this.particles.filter(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += p.gravity;
        p.vx *= 0.98;
        p.vy *= 0.98;
        p.alpha -= p.decay;
        return p.alpha > 0;
      });

      for (const p of this.particles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      requestAnimationFrame(() => this.animate());
    }
  }

  /* ──────────────────────────────────────────
     Initialization
     ────────────────────────────────────────── */
  function initViseBits() {
    // Aurora Hero
    const heroCanvas = document.getElementById('vise-hero-canvas');
    if (heroCanvas) {
      new AuroraHero(heroCanvas);
    }

    // Count Up
    document.querySelectorAll('[data-vise-countup]').forEach(el => {
      const target = parseFloat(el.dataset.viseCountup) || 0;
      const duration = parseInt(el.dataset.viseDuration) || 2000;
      const decimals = parseInt(el.dataset.viseDecimals) || 0;
      const suffix = el.dataset.viseSuffix || '';
      const prefix = el.dataset.visePrefix || '';
      new CountUp(el, { target, duration, decimals, suffix, prefix });
    });

    // Splash Cursor
    if (!window.__viseSplashInited) {
      new SplashCursor();
      window.__viseSplashInited = true;
    }
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initViseBits);
  } else {
    initViseBits();
  }

  /* ──────────────────────────────────────────
     Auto-apply effects to dynamic city cards
     ────────────────────────────────────────── */
  function applyCardEffects(container) {
    container.querySelectorAll('.city-card').forEach(el => {
      if (el.dataset.viseTilted) return;
      el.dataset.viseTilted = '1';
      new TiltedCard(el, { maxTilt: 6, scale: 1.03 });
      new SpotlightCard(el);
    });
  }

  const cardObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const node of m.addedNodes) {
        if (node.nodeType === 1) {
          if (node.matches?.('.city-card')) {
            applyCardEffects(node.parentElement || document);
          } else if (node.querySelectorAll) {
            applyCardEffects(node);
          }
        }
      }
    }
  });
  cardObserver.observe(document.body, { childList: true, subtree: true });

  // Also handle the first batch of city cards that might already be loaded
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => applyCardEffects(document), 500);
  });

  // Expose for dynamic use
  window.ViseBits = {
    AuroraHero,
    TiltedCard,
    SpotlightCard,
    CountUp,
    SplashCursor,
  };

})();

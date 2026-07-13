/* ═══════════════════════════════════════════════════════════════
   DECK CONTROLLER — navegación por pasos (slides)
   Avanza: Enter / Espacio / → / ↓ / click / rueda del mouse (snap)
   Retrocede: ← / ↑ / Backspace
   Overview: "O"   ·   Anexo directo: "A"   ·   Cerrar overview: Esc
═══════════════════════════════════════════════════════════════ */

const deck = document.getElementById('deck');
const steps = Array.from(document.querySelectorAll('#deck .step'));

let currentIndex = 0;
let currentStage = 0;

function totalStages(step) {
  if (window.stepStageCount) return window.stepStageCount(step.id);
  return 1;
}

function playStage(step, stageIndex) {
  if (window.playStepStage) window.playStepStage(step.id, stageIndex);
}

/* ── Reveal automático de .reveal dentro del paso activo ────────
   (los .reveal-manual quedan a cargo de los builds en charts.js) */

function autoRevealStep(step) {
  const reveals = step.querySelectorAll('.reveal');
  reveals.forEach((el, i) => {
    el.style.transitionDelay = (i * 0.08) + 's';
  });
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08 }
  );
  reveals.forEach((el) => io.observe(el));
}

// Prepara el reveal automático de todos los pasos una sola vez (al cargar):
// como los .step inactivos están visibility:hidden, el observer no dispara
// hasta que el paso se activa de verdad.
steps.forEach((step) => autoRevealStep(step));

/* ── Barras que crecen por ancho (.bar-fill / .ts-seg) ──────────
   Mismo mecanismo: solo disparan cuando el contenedor se hace visible. */

const barFills = document.querySelectorAll('.hc-bar__fill, .ts-seg');
barFills.forEach((bar) => { bar.style.width = '0%'; });
const barObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const pct = entry.target.dataset.width;
        if (pct) entry.target.style.width = pct + '%';
        barObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.6 }
);
barFills.forEach((bar) => barObserver.observe(bar));

/* ═══════════════════════════════════════════════════════════════
   NAVEGACIÓN ENTRE PASOS
═══════════════════════════════════════════════════════════════ */

function enterStep(index, { instant = false } = {}) {
  if (index < 0 || index >= steps.length) return;

  const prev = steps[currentIndex];
  const next = steps[index];

  if (prev && prev !== next) prev.classList.remove('step--active');

  currentIndex = index;
  const stages = totalStages(next);
  currentStage = instant ? stages - 1 : 0;

  next.classList.add('step--active');
  next.scrollTop = 0;

  if (instant) {
    for (let s = 0; s <= currentStage; s++) playStage(next, s);
  } else {
    playStage(next, 0);
  }

  updateProgress();
  history.replaceState(null, '', '#' + next.id);
}

function advance() {
  const step = steps[currentIndex];
  const stages = totalStages(step);
  if (currentStage < stages - 1) {
    currentStage++;
    playStage(step, currentStage);
  } else if (currentIndex < steps.length - 1) {
    enterStep(currentIndex + 1, { instant: false });
  }
}

function goBack() {
  if (currentIndex > 0) {
    enterStep(currentIndex - 1, { instant: true });
  }
}

function jumpToStep(index) {
  enterStep(index, { instant: true });
}

function jumpToAct(actValue) {
  const idx = steps.findIndex((s) => s.dataset.act === actValue);
  if (idx >= 0) jumpToStep(idx);
}

/* ═══════════════════════════════════════════════════════════════
   INDICADOR DE PROGRESO — 1 segmento por acto
═══════════════════════════════════════════════════════════════ */

const progressEl = document.getElementById('deck-progress');
const actGroups = []; // [{ act, firstIndex }]

steps.forEach((step, i) => {
  const act = step.dataset.act;
  if (act === 'anexo') return; // el anexo no cuenta como acto numerado
  const last = actGroups[actGroups.length - 1];
  if (!last || last.act !== act) actGroups.push({ act, firstIndex: i });
});

actGroups.forEach((group) => {
  const seg = document.createElement('button');
  seg.className = 'deck-progress__seg';
  seg.dataset.act = group.act;
  seg.setAttribute('aria-label', 'Ir al acto ' + group.act);
  seg.addEventListener('click', (e) => {
    e.stopPropagation();
    jumpToAct(group.act);
    seg.blur();
  });
  progressEl.appendChild(seg);
});

function updateProgress() {
  // Grupo de actos correspondiente al paso actual (el último cuyo primer
  // índice sea <= currentIndex — cubre también el caso "viendo el anexo").
  let activeGroup = null;
  actGroups.forEach((g) => { if (g.firstIndex <= currentIndex) activeGroup = g; });

  progressEl.querySelectorAll('.deck-progress__seg').forEach((seg) => {
    const segGroup = actGroups.find((g) => g.act === seg.dataset.act);
    const isActive = activeGroup === segGroup;
    const isDone = activeGroup && segGroup.firstIndex < activeGroup.firstIndex;
    seg.classList.toggle('is-active', isActive);
    seg.classList.toggle('is-done', !!isDone);
  });
}

/* ═══════════════════════════════════════════════════════════════
   OVERVIEW — grilla de todos los pasos ("O")
═══════════════════════════════════════════════════════════════ */

const overviewEl = document.getElementById('overview-grid');

function buildOverview() {
  const title = document.createElement('p');
  title.className = 'overview-grid__title';
  title.textContent = 'Overview — click para saltar · Esc para cerrar';
  overviewEl.appendChild(title);

  const cells = document.createElement('div');
  cells.className = 'overview-grid__cells';
  steps.forEach((step, i) => {
    const cell = document.createElement('button');
    cell.className = 'overview-cell';
    cell.dataset.index = i;
    const act = document.createElement('span');
    act.className = 'overview-cell__act';
    act.textContent = step.dataset.act === 'anexo' ? 'ANEXO' : ('ACTO ' + step.dataset.act);
    const label = document.createElement('span');
    label.className = 'overview-cell__label';
    label.textContent = step.dataset.label || step.id;
    cell.appendChild(act);
    cell.appendChild(label);
    cell.addEventListener('click', (e) => {
      e.stopPropagation();
      cell.blur();
      closeOverview();
      jumpToStep(i);
    });
    cells.appendChild(cell);
  });
  overviewEl.appendChild(cells);
}
buildOverview();

function openOverview() {
  overviewEl.classList.add('is-open');
  overviewEl.querySelectorAll('.overview-cell').forEach((cell) => {
    cell.classList.toggle('is-current', parseInt(cell.dataset.index, 10) === currentIndex);
  });
}

function closeOverview() {
  overviewEl.classList.remove('is-open');
}

function isOverviewOpen() {
  return overviewEl.classList.contains('is-open');
}

/* ═══════════════════════════════════════════════════════════════
   TECLADO
═══════════════════════════════════════════════════════════════ */

document.addEventListener('keydown', (e) => {
  // Solo Enter/Espacio ceden el paso al elemento enfocado (link, summary, etc.)
  // -- las demás teclas (flechas, O, A) siguen navegando el deck igual,
  // aunque haya quedado el foco en un botón tras un click.
  const activeTag = document.activeElement ? document.activeElement.tagName : '';
  const isInteractive = ['A', 'BUTTON', 'SUMMARY', 'INPUT', 'TEXTAREA'].includes(activeTag);
  if (isInteractive && (e.key === 'Enter' || e.key === ' ')) {
    return;
  }

  if (isOverviewOpen()) {
    if (e.key === 'Escape' || e.key.toLowerCase() === 'o') {
      e.preventDefault();
      closeOverview();
    }
    return;
  }

  switch (e.key) {
    case 'Enter':
    case ' ':
    case 'ArrowRight':
    case 'ArrowDown':
      e.preventDefault();
      advance();
      break;
    case 'ArrowLeft':
    case 'ArrowUp':
    case 'Backspace':
      e.preventDefault();
      goBack();
      break;
    case 'o':
    case 'O':
      e.preventDefault();
      openOverview();
      break;
    case 'a':
    case 'A':
      e.preventDefault();
      jumpToAct('anexo');
      break;
  }
});

/* ═══════════════════════════════════════════════════════════════
   CLICK PARA AVANZAR
═══════════════════════════════════════════════════════════════ */

deck.addEventListener('click', (e) => {
  if (e.target.closest('a, button, summary, .no-advance')) return;
  if (window.getSelection().toString().length > 0) return;
  const step = steps[currentIndex];
  if (step.id === 's-anexo') return; // lectura libre en el anexo
  advance();
});

/* ═══════════════════════════════════════════════════════════════
   RUEDA DEL MOUSE — avanza/retrocede por paso (con snap), respeta
   el scroll nativo mientras el contenido del paso no llegó al borde
═══════════════════════════════════════════════════════════════ */

let lastWheelTime = 0;
const WHEEL_COOLDOWN = 750;

deck.addEventListener('wheel', (e) => {
  if (isOverviewOpen()) return;
  const step = steps[currentIndex];
  const atTop = step.scrollTop <= 2;
  const atBottom = step.scrollTop + step.clientHeight >= step.scrollHeight - 2;

  if (e.deltaY > 0 && !atBottom) return;   // dejar scroll nativo dentro del paso
  if (e.deltaY < 0 && !atTop) return;

  e.preventDefault();
  const now = Date.now();
  if (now - lastWheelTime < WHEEL_COOLDOWN) return;
  lastWheelTime = now;

  if (e.deltaY > 0) advance();
  else if (e.deltaY < 0) goBack();
}, { passive: false });

/* ═══════════════════════════════════════════════════════════════
   PISTA DE TECLADO — se atenúa tras la primera interacción
═══════════════════════════════════════════════════════════════ */

const hintEl = document.getElementById('deck-hint');
let hintDismissed = false;
function dismissHint() {
  if (hintDismissed) return;
  hintDismissed = true;
  hintEl.classList.add('is-hidden');
}
['keydown', 'wheel', 'click'].forEach((evt) => {
  document.addEventListener(evt, dismissHint, { once: true, passive: true });
});

/* ═══════════════════════════════════════════════════════════════
   ARRANQUE — respeta #hash si vino de un link directo
═══════════════════════════════════════════════════════════════ */

(function init() {
  const hashId = location.hash ? location.hash.slice(1) : null;
  const hashIndex = hashId ? steps.findIndex((s) => s.id === hashId) : -1;

  if (hashIndex >= 0) {
    enterStep(hashIndex, { instant: true });
  } else {
    enterStep(0, { instant: false });
  }
})();

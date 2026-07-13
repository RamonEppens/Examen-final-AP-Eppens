/* ═══════════════════════════════════════════════════════════════
   CHARTS — SVG dibujado a mano, sin librerías externas.
   Reglas de geometría: nada puntiagudo, nada cuadrado.
   - Barras: cápsulas (radio = mitad del grosor)
   - Líneas: gruesas, curva suave (Catmull-Rom), extremos/uniones redondeados
   - Puntos: círculos
   - Bandas: área curva con relleno suave
   - Sin gridlines; ejes (si los hay) en gris muy claro con cabos redondeados
═══════════════════════════════════════════════════════════════ */

const SVG_NS = 'http://www.w3.org/2000/svg';

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const k in attrs) el.setAttribute(k, attrs[k]);
  return el;
}

function fmtEs(n, decimals = 0) {
  return n.toLocaleString('es-AR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/* ── Escalas ─────────────────────────────────────────────────── */

function linearScale([d0, d1], [r0, r1]) {
  return (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
}

function logScale([d0, d1], [r0, r1]) {
  const l0 = Math.log10(d0), l1 = Math.log10(d1);
  return (v) => r0 + ((Math.log10(v) - l0) / (l1 - l0)) * (r1 - r0);
}

/* ── Curvas suaves (Catmull-Rom → Bézier cúbica) ────────────────
   Uniform Catmull-Rom, tensión estándar (factor 6). Produce curvas
   suaves que pasan exactamente por cada punto, sin quiebres rectos. */

function catmullSegments(pts) {
  const segs = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i === 0 ? i : i - 1];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[i + 2 < pts.length ? i + 2 : i + 1];
    const c1x = p1[0] + (p2[0] - p0[0]) / 6;
    const c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6;
    const c2y = p2[1] - (p3[1] - p1[1]) / 6;
    segs.push(`C${c1x.toFixed(2)},${c1y.toFixed(2)} ${c2x.toFixed(2)},${c2y.toFixed(2)} ${p2[0].toFixed(2)},${p2[1].toFixed(2)}`);
  }
  return segs;
}

function smoothLinePath(pts) {
  if (pts.length < 2) return '';
  if (pts.length === 2) return `M${pts[0][0].toFixed(2)},${pts[0][1].toFixed(2)} L${pts[1][0].toFixed(2)},${pts[1][1].toFixed(2)}`;
  return `M${pts[0][0].toFixed(2)},${pts[0][1].toFixed(2)} ` + catmullSegments(pts).join(' ');
}

function smoothAreaPath(topPts, bottomPts) {
  const bottomRev = bottomPts.slice().reverse();
  return (
    `M${topPts[0][0].toFixed(2)},${topPts[0][1].toFixed(2)} ` +
    catmullSegments(topPts).join(' ') + ' ' +
    `L${bottomRev[0][0].toFixed(2)},${bottomRev[0][1].toFixed(2)} ` +
    catmullSegments(bottomRev).join(' ') + ' Z'
  );
}

/* ── Contador animado (count-up) ────────────────────────────────
   easeOutCubic, formatea con separador de miles es-AR */

function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

function animateCount(el, target, { duration = 1400, decimals = 0, prefix = '', suffix = '' } = {}) {
  const start = performance.now();
  function tick(now) {
    const t = Math.min(1, (now - start) / duration);
    const val = target * easeOutCubic(t);
    el.textContent = prefix + fmtEs(val, decimals) + suffix;
    if (t < 1) requestAnimationFrame(tick);
    else el.textContent = prefix + fmtEs(target, decimals) + suffix;
  }
  requestAnimationFrame(tick);
}

/* ── Observer genérico: dispara callback una sola vez al entrar ── */

function onEnter(el, callback, threshold = 0.35) {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          callback();
          io.unobserve(entry.target);
        }
      });
    },
    { threshold }
  );
  io.observe(el);
}

/* ── Dibuja una línea con animación de "trazado" (dash reveal) ─── */

function drawLineIn(pathEl, duration = 1500, delay = 0) {
  const len = pathEl.getTotalLength();
  pathEl.style.strokeDasharray = `${len}`;
  pathEl.style.strokeDashoffset = `${len}`;
  pathEl.getBoundingClientRect(); // fuerza reflow
  pathEl.style.transition = `stroke-dashoffset ${duration}ms cubic-bezier(.25,.46,.45,.94) ${delay}ms`;
  requestAnimationFrame(() => { pathEl.style.strokeDashoffset = '0'; });
}

/* ── Contadores genéricos declarativos ──────────────────────────
   <span class="countup" data-target="24251" data-decimals="0"
         data-prefix="" data-suffix="">0</span>
   Los que viven dentro de un .reveal-manual quedan gateados a un
   build explícito (ver STEP_STAGES) en vez de dispararse solos. */

function triggerCountUp(el) {
  const target = parseFloat(el.dataset.target);
  if (Number.isNaN(target)) return;
  const decimals = parseInt(el.dataset.decimals || '0', 10);
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const duration = parseInt(el.dataset.duration || '1400', 10);
  animateCount(el, target, { duration, decimals, prefix, suffix });
}

function initCountUps() {
  document.querySelectorAll('.countup').forEach((el) => {
    if (el.closest('.reveal-manual')) return; // disparado a mano por un build
    onEnter(el, () => triggerCountUp(el), 0.5);
  });
}

/* ── Reveal genérico para grupos de chips ───────────────────────
   <div class="chip-row"> <span class="chip">...</span> ... </div>
   Igual que arriba: los .reveal-manual quedan gateados a un build. */

function triggerChipRow(row) {
  row.querySelectorAll('.chip').forEach((chip, i) => {
    setTimeout(() => chip.classList.add('visible'), i * 220);
  });
}

function initChipReveal() {
  document.querySelectorAll('.chip-row').forEach((row) => {
    if (row.classList.contains('reveal-manual') || row.closest('.reveal-manual')) return;
    onEnter(row, () => triggerChipRow(row), 0.4);
  });
}

/* ── Reveal manual genérico: agrega .visible a un selector ──────
   Usado por los builds tipo PowerPoint (ver STEP_STAGES). */

function revealManual(selector) {
  document.querySelectorAll(selector).forEach((el) => el.classList.add('visible'));
}

/* ── Barras cápsula horizontales genéricas ──────────────────────
   items: [{ label, display, pct, best }] */

function renderBarRows(containerId, items) {
  const root = document.getElementById(containerId);
  if (!root) return;

  items.forEach((item, i) => {
    const row = document.createElement('div');
    row.className = 'bar-row' + (item.best ? ' bar-row--best' : '');
    row.style.transitionDelay = `${i * 100}ms`;

    const top = document.createElement('div');
    top.className = 'bar-row__top';
    const label = document.createElement('span');
    label.className = 'bar-row__label';
    label.textContent = item.label;
    const val = document.createElement('span');
    val.className = 'bar-row__value';
    val.textContent = item.display;
    top.appendChild(label);
    top.appendChild(val);
    row.appendChild(top);

    const track = document.createElement('div');
    track.className = 'bar-track';
    const fill = document.createElement('div');
    fill.className = 'bar-fill';
    track.appendChild(fill);
    row.appendChild(track);

    root.appendChild(row);

    onEnter(row, () => {
      row.classList.add('visible');
      requestAnimationFrame(() => { fill.style.width = item.pct.toFixed(2) + '%'; });
    }, 0.4);
  });
}

function renderRmseLadder(containerId, data) {
  const max = Math.max(...data.ladder.map(d => d.rmse));
  const items = data.ladder.map((d, i) => ({
    label: d.name,
    display: `${d.rmse.toFixed(3)} ± ${d.std.toFixed(3)}`,
    pct: (d.rmse / max) * 100,
    best: i === data.ladder.length - 1,
  }));
  renderBarRows(containerId, items);
}

function renderTopMechanicsBars(containerId, data, topN = 8) {
  const mechs = data.top_mechanics.slice(0, topN);
  const max = Math.max(...mechs.map(m => m.n));
  const items = mechs.map(m => ({
    label: m.name,
    display: fmtEs(m.n),
    pct: (m.n / max) * 100,
  }));
  renderBarRows(containerId, items);
}

function renderTopImportances(containerId, data, topN = 8) {
  const top = data.top10_importances.slice(0, topN);
  const max = Math.max(...top.map(d => d.value));
  const items = top.map((d, i) => ({
    label: d.feature,
    display: fmtEs(d.value),
    pct: (d.value / max) * 100,
    best: i === 0,
  }));
  renderBarRows(containerId, items);
}


/* ═══════════════════════════════════════════════════════════════
   FILA DE EJEMPLO — tarjeta horizontal con un juego real del
   dataset (Acto 3b: "El dataset por dentro"), cargada desde
   presentacion/data/sample_row.js — nada de esto es inventado.
═══════════════════════════════════════════════════════════════ */

function makeEl(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderSampleCard(containerId, row) {
  const root = document.getElementById(containerId);
  if (!root) return;

  const name = makeEl('div', 'sample-card__id');
  name.appendChild(makeEl('span', 'sample-card__name', row.name));
  name.appendChild(makeEl('span', 'sample-card__meta', `ID ${row.game_id} · ${row.year}`));

  const fields = makeEl('div', 'sample-card__fields');
  const specs = [
    ['weight', row.weight.toFixed(2)],
    ['jugadores', `${row.min_players}–${row.max_players}`],
    ['duración', `${row.min_playtime}–${row.max_playtime} min`],
    ['edad mín.', `${row.min_age}+`],
    ['mecánicas', row.mechanics_sample.join(' · ')],
  ];
  specs.forEach(([label, value]) => {
    const f = makeEl('div', 'sample-field');
    f.appendChild(makeEl('span', 'sample-field__label', label));
    f.appendChild(makeEl('span', 'sample-field__value', value));
    fields.appendChild(f);
  });

  const target = makeEl('div', 'sample-card__target');
  target.appendChild(makeEl('span', 'sample-card__target-label', 'target'));
  target.appendChild(makeEl('span', 'sample-card__target-value', row.average.toFixed(2)));

  root.appendChild(name);
  root.appendChild(fields);
  root.appendChild(target);
}

function renderSchemaGrid(containerId, row) {
  const root = document.getElementById(containerId);
  if (!root) return;

  const groups = [
    { label: 'Identificación', fields: ['game_id', 'name', 'year'] },
    {
      label: 'Ficha técnica → features',
      fields: ['weight', 'min_players', 'max_players', 'min_playtime', 'max_playtime', 'min_age', 'mechanics', 'categories', 'designers', 'publishers'],
    },
    {
      label: 'Comunidad',
      fields: [
        { name: 'average', target: true },
        { name: 'users_rated', excluded: true },
        { name: 'bayes_average', excluded: true },
        { name: 'rank', excluded: true },
      ],
    },
  ];

  groups.forEach((group) => {
    const col = makeEl('div', 'schema-col');
    col.appendChild(makeEl('span', 'schema-col__label', group.label));
    const list = makeEl('div', 'schema-col__fields');
    group.fields.forEach((f) => {
      if (typeof f === 'string') {
        list.appendChild(makeEl('span', 'schema-field', f));
        return;
      }
      const tag = makeEl('span', 'schema-field' + (f.excluded ? ' schema-field--excluded' : ' schema-field--target'), f.name);
      list.appendChild(tag);
    });
    col.appendChild(list);
    if (group.label === 'Comunidad') {
      col.appendChild(makeEl('span', 'schema-col__note', 'excluidas — leakage / no disponibles pre-lanzamiento'));
    }
    root.appendChild(col);
  });
}

function renderSampleFooter(elId, row, cleanFinal) {
  const node = document.getElementById(elId);
  if (!node) return;
  node.textContent = `${fmtEs(cleanFinal)} filas × ${row.n_raw_fields} campos crudos → ${row.n_features} features tras encoding.`;
}


/* ═══════════════════════════════════════════════════════════════
   1. PIPELINE EN Y — veredicto (GitHub) + ficha (API) → unidos por ID
   Se dibuja una sola vez, oculto; cada parte se revela cuando el
   paso de texto correspondiente (data-step) entra al viewport
   (ver initPipelineSteps más abajo) — el diagrama "se arma" a
   medida que se lee la narrativa.
═══════════════════════════════════════════════════════════════ */

function renderPipelineMerge(containerId) {
  const root = document.getElementById(containerId);
  if (!root) return;

  const W = 720, H = 210;
  const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, class: 'pipeline-svg', 'aria-hidden': 'true' });

  const nodeW = 300, nodeH = 88;
  const nodeA = { x: 20, y: 10 };
  const nodeB = { x: 400, y: 10 };
  nodeA.cx = nodeA.x + nodeW / 2;
  nodeB.cx = nodeB.x + nodeW / 2;
  const bottomY = nodeA.y + nodeH;
  const merge = { x: 360, y: bottomY + 74 };

  // Conectores (curva suave) + punto de fusión + etiqueta "ID" -- paso 2
  const connA = svgEl('path', {
    d: smoothLinePath([[nodeA.cx, bottomY], [nodeA.cx, bottomY + 38], [merge.x, merge.y]]),
    class: 'pipeline-connector', fill: 'none', 'data-step': '2',
  });
  const connB = svgEl('path', {
    d: smoothLinePath([[nodeB.cx, bottomY], [nodeB.cx, bottomY + 38], [merge.x, merge.y]]),
    class: 'pipeline-connector', fill: 'none', 'data-step': '2',
  });
  svg.appendChild(connA);
  svg.appendChild(connB);

  const idLabel = svgEl('text', {
    x: merge.x, y: merge.y - 16, class: 'pipeline-id-label', 'text-anchor': 'middle', 'data-step': '2',
  });
  idLabel.textContent = 'ID';
  svg.appendChild(idLabel);

  const mergeDot = svgEl('circle', { cx: merge.x, cy: merge.y, r: 6, class: 'pipeline-connector-dot', 'data-step': '2' });
  svg.appendChild(mergeDot);

  function addNode(n, label, sub, step) {
    const g = svgEl('g', { class: 'pipeline-node', 'data-step': step });
    g.appendChild(svgEl('rect', {
      x: n.x, y: n.y, width: nodeW, height: nodeH, rx: 20, ry: 20, class: 'pipeline-node-rect',
    }));
    const l = svgEl('text', { x: n.cx, y: n.y + 38, class: 'pipeline-node-label', 'text-anchor': 'middle' });
    l.textContent = label;
    const s = svgEl('text', { x: n.cx, y: n.y + 60, class: 'pipeline-node-sub', 'text-anchor': 'middle' });
    s.textContent = sub;
    g.appendChild(l);
    g.appendChild(s);
    svg.appendChild(g);
  }

  addNode(nodeA, 'Veredicto', 'ranking diario · GitHub', '0');
  addNode(nodeB, 'Ficha', 'API oficial · BGG', '1');

  root.appendChild(svg);
}

function revealPipelineStep(containerId, step) {
  const root = document.getElementById(containerId);
  if (!root) return;
  root.querySelectorAll(`[data-step="${step}"]`).forEach((el, i) => {
    setTimeout(() => {
      if (el.tagName === 'path') drawLineIn(el, 700);
      else el.classList.add('visible');
    }, i * 150);
  });
}


/* ═══════════════════════════════════════════════════════════════
   2. GRÁFICO EMBUDO — varianza del rating vs. cantidad de votos
═══════════════════════════════════════════════════════════════ */

function renderFunnelChart(containerId, funnel) {
  const root = document.getElementById(containerId);
  if (!root) return;

  const W = 640, H = 360;
  const M = { top: 28, right: 24, bottom: 44, left: 24 };
  const plotW = W - M.left - M.right;
  const plotH = H - M.top - M.bottom;

  const votesExtent = [50, Math.max(...funnel.scatter.map(d => d.votes)) * 1.05];
  const ratingExtent = [
    Math.min(...funnel.bins.map(b => b.p10)) - 0.3,
    Math.max(...funnel.bins.map(b => b.p90)) + 0.3,
  ];

  const x = logScale(votesExtent, [M.left, M.left + plotW]);
  const y = linearScale(ratingExtent, [M.top + plotH, M.top]);

  const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart-svg', role: 'img',
    'aria-label': 'Variación del rating según cantidad de votos: la dispersión se reduce a medida que crecen los votos' });

  svg.appendChild(svgEl('line', {
    x1: M.left, y1: M.top + plotH, x2: M.left + plotW, y2: M.top + plotH,
    class: 'chart-axis-line',
  }));

  const ticks = [50, 200, 1000, 5000, 20000, 100000].filter(t => t <= votesExtent[1]);
  ticks.forEach((t) => {
    const tx = x(t);
    const label = svgEl('text', { x: tx, y: M.top + plotH + 22, class: 'chart-tick', 'text-anchor': 'middle' });
    label.textContent = t >= 1000 ? `${t / 1000}k` : `${t}`;
    svg.appendChild(label);
  });
  const axisCaption = svgEl('text', { x: M.left + plotW / 2, y: H - 4, class: 'chart-axis-caption', 'text-anchor': 'middle' });
  axisCaption.textContent = 'cantidad de votos (escala log)';
  svg.appendChild(axisCaption);

  const topPts = funnel.bins.map(b => [x(b.votes_mid), y(b.p90)]);
  const botPts = funnel.bins.map(b => [x(b.votes_mid), y(b.p10)]);
  const band = svgEl('path', { d: smoothAreaPath(topPts, botPts), class: 'chart-band' });
  svg.appendChild(band);

  const scatterG = svgEl('g', { class: 'chart-scatter' });
  funnel.scatter.forEach((d) => {
    scatterG.appendChild(svgEl('circle', { cx: x(d.votes), cy: y(d.rating), r: 2.3, class: 'chart-dot' }));
  });
  svg.appendChild(scatterG);

  const meanPts = funnel.bins.map(b => [x(b.votes_mid), y(b.mean)]);
  const meanLine = svgEl('path', { d: smoothLinePath(meanPts), class: 'chart-line' });
  svg.appendChild(meanLine);

  const last = funnel.bins[funnel.bins.length - 1];
  const lx = x(last.votes_mid), ly = y(last.mean);
  svg.appendChild(svgEl('circle', { cx: lx, cy: ly, r: 5, class: 'chart-end-dot' }));

  const labelWide = svgEl('text', { x: x(votesExtent[0]) + 6, y: y(funnel.bins[0].p10) + 16, class: 'chart-direct-label' });
  labelWide.textContent = 'pocos votos → rating volátil';
  svg.appendChild(labelWide);

  const labelNarrow = svgEl('text', { x: x(votesExtent[1]) - 6, y: y(last.p90) - 10, class: 'chart-direct-label', 'text-anchor': 'end' });
  labelNarrow.textContent = 'muchos votos → rating estable';
  svg.appendChild(labelNarrow);

  root.appendChild(svg);

  onEnter(root, () => {
    band.classList.add('visible');
    setTimeout(() => scatterG.classList.add('visible'), 150);
    setTimeout(() => drawLineIn(meanLine, 1300), 250);
    setTimeout(() => { root.querySelector('.chart-end-dot').classList.add('visible'); }, 1550);
    root.querySelectorAll('.chart-direct-label').forEach((l, i) => {
      setTimeout(() => l.classList.add('visible'), 1650 + i * 120);
    });
  }, 0.3);
}


/* ═══════════════════════════════════════════════════════════════
   3. SESGO TEMPORAL — media por año + banda P25–P75
═══════════════════════════════════════════════════════════════ */

function renderTemporalChart(containerId, temporal) {
  const root = document.getElementById(containerId);
  if (!root) return;

  const W = 640, H = 340;
  const M = { top: 28, right: 20, bottom: 40, left: 24 };
  const plotW = W - M.left - M.right;
  const plotH = H - M.top - M.bottom;

  const years = temporal.years;
  const yearExtent = [years[0], years[years.length - 1]];
  const ratingExtent = [
    Math.min(...temporal.p25) - 0.25,
    Math.max(...temporal.p75) + 0.25,
  ];

  const x = linearScale(yearExtent, [M.left, M.left + plotW]);
  const y = linearScale(ratingExtent, [M.top + plotH, M.top]);

  const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart-svg', role: 'img',
    'aria-label': 'Rating promedio por año de publicación: estable hasta 2010, en ascenso sostenido después' });

  svg.appendChild(svgEl('line', {
    x1: M.left, y1: M.top + plotH, x2: M.left + plotW, y2: M.top + plotH,
    class: 'chart-axis-line',
  }));

  const tickYears = [1971, 1980, 1990, 2000, 2010, 2020, 2026].filter(t => t >= yearExtent[0] && t <= yearExtent[1]);
  tickYears.forEach((t) => {
    const label = svgEl('text', { x: x(t), y: M.top + plotH + 22, class: 'chart-tick', 'text-anchor': 'middle' });
    label.textContent = t;
    svg.appendChild(label);
  });

  const topPts = years.map((yr, i) => [x(yr), y(temporal.p75[i])]);
  const botPts = years.map((yr, i) => [x(yr), y(temporal.p25[i])]);
  const band = svgEl('path', { d: smoothAreaPath(topPts, botPts), class: 'chart-band' });
  svg.appendChild(band);

  const meanPts = years.map((yr, i) => [x(yr), y(temporal.mean[i])]);
  const meanLine = svgEl('path', { d: smoothLinePath(meanPts), class: 'chart-line' });
  svg.appendChild(meanLine);

  const flatIdx = years.indexOf(2000) >= 0 ? years.indexOf(2000) : 0;
  const flatPt = meanPts[flatIdx];
  svg.appendChild(svgEl('circle', { cx: flatPt[0], cy: flatPt[1], r: 4.5, class: 'chart-end-dot chart-end-dot--mid' }));
  const flatLabel = svgEl('text', { x: flatPt[0], y: flatPt[1] - 16, class: 'chart-direct-label', 'text-anchor': 'middle' });
  flatLabel.textContent = `~${temporal.mean[flatIdx].toFixed(1)} plano hasta 2010`;
  svg.appendChild(flatLabel);

  const lastPt = meanPts[meanPts.length - 1];
  svg.appendChild(svgEl('circle', { cx: lastPt[0], cy: lastPt[1], r: 5.5, class: 'chart-end-dot' }));
  const lastLabel = svgEl('text', { x: lastPt[0] - 8, y: lastPt[1] - 14, class: 'chart-direct-label chart-direct-label--accent', 'text-anchor': 'end' });
  lastLabel.textContent = `${temporal.mean[temporal.mean.length - 1].toFixed(2)} en ${years[years.length - 1]}`;
  svg.appendChild(lastLabel);

  root.appendChild(svg);

  onEnter(root, () => {
    band.classList.add('visible');
    setTimeout(() => drawLineIn(meanLine, 1600), 150);
    setTimeout(() => { root.querySelectorAll('.chart-end-dot').forEach(d => d.classList.add('visible')); }, 1750);
    setTimeout(() => { root.querySelectorAll('.chart-direct-label').forEach(l => l.classList.add('visible')); }, 1900);
  }, 0.3);
}


/* ═══════════════════════════════════════════════════════════════
   4. WEIGHT vs. AVERAGE — scatter + línea de tendencia suave
═══════════════════════════════════════════════════════════════ */

function renderScatterTrendChart(containerId, weightAvg) {
  const root = document.getElementById(containerId);
  if (!root) return;

  const W = 640, H = 340;
  const M = { top: 24, right: 20, bottom: 40, left: 24 };
  const plotW = W - M.left - M.right;
  const plotH = H - M.top - M.bottom;

  const xExtent = [1, 5];
  const yVals = weightAvg.scatter.map(d => d.y);
  const yExtent = [Math.min(...yVals) - 0.3, Math.max(...yVals) + 0.3];

  const x = linearScale(xExtent, [M.left, M.left + plotW]);
  const y = linearScale(yExtent, [M.top + plotH, M.top]);

  const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart-svg', role: 'img',
    'aria-label': `Relación entre complejidad (weight) y rating promedio: correlación de Spearman ${weightAvg.spearman}` });

  svg.appendChild(svgEl('line', {
    x1: M.left, y1: M.top + plotH, x2: M.left + plotW, y2: M.top + plotH,
    class: 'chart-axis-line',
  }));

  [1, 2, 3, 4, 5].forEach((t) => {
    const label = svgEl('text', { x: x(t), y: M.top + plotH + 22, class: 'chart-tick', 'text-anchor': 'middle' });
    label.textContent = t;
    svg.appendChild(label);
  });
  const axisCaption = svgEl('text', { x: M.left + plotW / 2, y: H - 4, class: 'chart-axis-caption', 'text-anchor': 'middle' });
  axisCaption.textContent = 'weight (complejidad percibida, 1–5)';
  svg.appendChild(axisCaption);

  const scatterG = svgEl('g', { class: 'chart-scatter' });
  weightAvg.scatter.forEach((d) => {
    scatterG.appendChild(svgEl('circle', { cx: x(d.x), cy: y(d.y), r: 2.2, class: 'chart-dot' }));
  });
  svg.appendChild(scatterG);

  const trendPts = weightAvg.trend.map(d => [x(d.x), y(d.y)]);
  const trendLine = svgEl('path', { d: smoothLinePath(trendPts), class: 'chart-line' });
  svg.appendChild(trendLine);

  const last = weightAvg.trend[weightAvg.trend.length - 1];
  svg.appendChild(svgEl('circle', { cx: x(last.x), cy: y(last.y), r: 5, class: 'chart-end-dot' }));

  root.appendChild(svg);

  onEnter(root, () => {
    setTimeout(() => scatterG.classList.add('visible'), 100);
    setTimeout(() => drawLineIn(trendLine, 1300), 200);
    setTimeout(() => { root.querySelector('.chart-end-dot').classList.add('visible'); }, 1500);
  }, 0.3);
}


/* ═══════════════════════════════════════════════════════════════
   5. YEAR × WEIGHT — línea plana (sin tendencia real)
═══════════════════════════════════════════════════════════════ */

function renderYearWeightChart(containerId, yearWeight) {
  const root = document.getElementById(containerId);
  if (!root) return;

  const W = 640, H = 300;
  const M = { top: 28, right: 20, bottom: 40, left: 24 };
  const plotW = W - M.left - M.right;
  const plotH = H - M.top - M.bottom;

  const years = yearWeight.years;
  const yearExtent = [years[0], years[years.length - 1]];
  const wExtent = [
    Math.min(...yearWeight.mean_weight) - 0.15,
    Math.max(...yearWeight.mean_weight) + 0.15,
  ];

  const x = linearScale(yearExtent, [M.left, M.left + plotW]);
  const y = linearScale(wExtent, [M.top + plotH, M.top]);

  const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart-svg', role: 'img',
    'aria-label': `Complejidad promedio por año de publicación: sin tendencia, correlación de Spearman ${yearWeight.spearman}` });

  svg.appendChild(svgEl('line', {
    x1: M.left, y1: M.top + plotH, x2: M.left + plotW, y2: M.top + plotH,
    class: 'chart-axis-line',
  }));

  const tickYears = [1971, 1980, 1990, 2000, 2010, 2020, 2026].filter(t => t >= yearExtent[0] && t <= yearExtent[1]);
  tickYears.forEach((t) => {
    const label = svgEl('text', { x: x(t), y: M.top + plotH + 22, class: 'chart-tick', 'text-anchor': 'middle' });
    label.textContent = t;
    svg.appendChild(label);
  });

  // Banda de referencia (media global +/- desvio) -- ancla visual de "estabilidad"
  const mean = yearWeight.mean_weight.reduce((a, b) => a + b, 0) / yearWeight.mean_weight.length;
  const band = svgEl('rect', {
    x: M.left, y: y(mean + 0.12), width: plotW, height: y(mean - 0.12) - y(mean + 0.12),
    rx: 10, class: 'chart-band chart-band--flat',
  });
  svg.appendChild(band);

  const linePts = years.map((yr, i) => [x(yr), y(yearWeight.mean_weight[i])]);
  const line = svgEl('path', { d: smoothLinePath(linePts), class: 'chart-line chart-line--muted' });
  svg.appendChild(line);

  const rhoLabel = svgEl('text', { x: M.left + plotW / 2, y: M.top + 6, class: 'chart-direct-label chart-direct-label--accent', 'text-anchor': 'middle' });
  rhoLabel.textContent = `ρ = ${yearWeight.spearman.toFixed(2)}  →  prácticamente sin correlación`;
  svg.appendChild(rhoLabel);

  root.appendChild(svg);

  onEnter(root, () => {
    band.classList.add('visible');
    setTimeout(() => drawLineIn(line, 1500), 150);
    setTimeout(() => { rhoLabel.classList.add('visible'); }, 1700);
  }, 0.3);
}


/* ═══════════════════════════════════════════════════════════════
   BUILDS TIPO POWERPOINT — secuencias internas dentro de un paso
   Cada entrada es un array de funciones (una por build extra, sin
   contar el build 0 que corresponde a lo que ya revela el reveal
   automático .reveal). El controlador del deck (script.js) llama
   window.playStepStage(stepId, stageIndex) al avanzar dentro del
   paso; stageIndex 0 se dispara solo al entrar al paso.
═══════════════════════════════════════════════════════════════ */

const STEP_STAGES = {
  's-acto3': [
    () => { // 0: nodo "Veredicto" + primer párrafo
      revealPipelineStep('pipeline-merge', '0');
      revealManual('#s-acto3 .pipeline-step:nth-of-type(1)');
    },
    () => { // 1: nodo "Ficha" + segundo párrafo
      revealPipelineStep('pipeline-merge', '1');
      revealManual('#s-acto3 .pipeline-step:nth-of-type(2)');
    },
    () => { // 2: conectores + "ID" + tercer párrafo
      revealPipelineStep('pipeline-merge', '2');
      revealManual('#s-acto3 .pipeline-step:nth-of-type(3)');
    },
    () => { // 3: cascada de limpieza + chips + nota
      revealManual('#s-acto3 .count-flow');
      document.querySelectorAll('#s-acto3 .count-flow .countup').forEach(triggerCountUp);
      const chipRow = document.querySelector('#s-acto3 .chip-row');
      if (chipRow) { chipRow.classList.add('visible'); triggerChipRow(chipRow); }
      revealManual('#s-acto3 .one-liner');
    },
  ],
  's-acto4a': [() => {}, () => revealManual('#s-acto4a .eda-resolution')],
  's-acto4b': [() => {}, () => revealManual('#s-acto4b .eda-resolution')],
  's-acto4c': [() => {}, () => revealManual('#s-acto4c .eda-resolution')],
  's-acto4d': [() => {}, () => revealManual('#s-acto4d .eda-resolution')],
};

function playStepStage(stepId, stageIndex) {
  const stages = STEP_STAGES[stepId];
  if (!stages || !stages[stageIndex]) return;
  stages[stageIndex]();
}

function stepStageCount(stepId) {
  return (STEP_STAGES[stepId] || [null]).length;
}

window.playStepStage = playStepStage;
window.stepStageCount = stepStageCount;


/* ═══════════════════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  initCountUps();
  initChipReveal();

  if (document.getElementById('pipeline-merge')) {
    renderPipelineMerge('pipeline-merge');
  }

  if (window.DATA_SAMPLE_ROW) {
    renderSampleCard('sample-card', window.DATA_SAMPLE_ROW);
    renderSchemaGrid('schema-grid', window.DATA_SAMPLE_ROW);
    const cleanFinal = (window.DATA_DATASET_PIPELINE && window.DATA_DATASET_PIPELINE.clean_final) || 24251;
    renderSampleFooter('sample-footer', window.DATA_SAMPLE_ROW, cleanFinal);
  }

  if (window.DATA_EDA_TARGET) {
    renderFunnelChart('chart-funnel', window.DATA_EDA_TARGET.funnel);
    renderTemporalChart('chart-temporal', window.DATA_EDA_TARGET.temporal);
  }

  if (window.DATA_EDA_FEATURES) {
    renderScatterTrendChart('chart-weight-avg', window.DATA_EDA_FEATURES.weight_avg);
    renderYearWeightChart('chart-year-weight', window.DATA_EDA_FEATURES.year_weight);
    renderTopMechanicsBars('bars-mechanics-annex', window.DATA_EDA_FEATURES);
  }

  if (window.DATA_MODEL_SELECTION) {
    renderRmseLadder('bars-ladder', window.DATA_MODEL_SELECTION);
  }

  if (window.DATA_MODEL_FINAL) {
    renderTopImportances('bars-importances', window.DATA_MODEL_FINAL);
  }
});

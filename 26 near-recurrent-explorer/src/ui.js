/**
 * Site UI wiring — FPEV Stage-3 Execute, phase P4.
 * No build step, no framework (D4). Hand-rolled SVG for heatmap/chart (D1).
 * Uses rdpv.js + bpr.js (loaded as plain scripts before this file).
 */

const REF = { AM: 0.15, PM: 0.19, minLen: 3 };
const DOW_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const state = {
  manifest: null,
  stationCache: new Map(), // vds -> loaded json
  selectedVds: null,
  period: 'AM', // 'AM' | 'PM'
  eps: REF.AM,
  minLen: REF.minLen,
};

async function loadManifest() {
  const res = await fetch('data/manifest.json');
  return res.json();
}

async function loadStation(vds) {
  if (state.stationCache.has(vds)) return state.stationCache.get(vds);
  const res = await fetch(`data/${vds}.json`);
  const json = await res.json();
  state.stationCache.set(vds, json);
  return json;
}

// ---------------------------------------------------------------- map ----

function initMap(manifest) {
  const map = L.map('map', { scrollWheelZoom: false }).setView([33.9, -118.1], 9);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 15,
  }).addTo(map);

  for (const s of manifest.stations) {
    if (s.lat == null || s.lon == null) continue;
    const partial = s.excluded_periods.length > 0;
    const marker = L.circleMarker([s.lat, s.lon], {
      radius: 9,
      color: '#0f1420',
      weight: 2,
      fillColor: partial ? '#f0883e' : '#3fb950',
      fillOpacity: 0.9,
    }).addTo(map);
    marker.bindTooltip(`${s.label} (${s.corridor})`);
    marker.on('click', () => selectStation(s.vds));
  }
  return map;
}

// ------------------------------------------------------------ selection --

async function selectStation(vds) {
  state.selectedVds = vds;
  const s = state.manifest.stations.find((st) => st.vds === vds);
  document.getElementById('station-title').textContent = `${s.label} — ${s.corridor}`;
  document.getElementById('period-toggle').hidden = false;

  // default to an eligible period if the current selection is excluded here
  if (s.excluded_periods.includes(state.period) && s.excluded_periods.length < 2) {
    state.period = state.period === 'AM' ? 'PM' : 'AM';
  }
  updatePeriodToggleUI();
  await loadStation(vds);
  render();
}

function updatePeriodToggleUI() {
  document.querySelectorAll('#period-toggle .toggle').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.period === state.period);
  });
}

// --------------------------------------------------------------- render --

function currentStationMeta() {
  return state.manifest.stations.find((s) => s.vds === state.selectedVds);
}

function computeForCurrentSelection() {
  const station = state.stationCache.get(state.selectedVds);
  const dp = station.daily_peaks;
  const weekNums = computeWeekNums(dp.date);
  const isAm = state.period === 'AM';
  const period = isAm ? 'morning-peak' : 'afternoon-peak';

  const facetResults = [];
  for (let dow = 0; dow < 7; dow++) {
    const idx = [];
    for (let i = 0; i < dp.date.length; i++) {
      if (dp.is_am[i] === isAm && dp.dow[i] === dow) idx.push(i);
    }
    const facet = {
      date: idx.map((i) => dp.date[i]),
      weeks: idx.map((i) => weekNums[i]),
      startHours: idx.map((i) => dp.start_h[i]),
      endHours: idx.map((i) => dp.end_h[i]),
      demand: idx.map((i) => dp.demand[i] * station.lane_count),
      traveltime: idx.map((i) => dp.traveltime[i]),
    };
    facetResults.push(classifyFacetRdpv(facet, period, state.eps, state.eps, state.minLen));
  }
  const { points, fit } = calibrateStationPeriod(facetResults, station.zeta_h_per_mi);
  return { facetResults, points, fit };
}

function render() {
  if (!state.selectedVds) return;
  const meta = currentStationMeta();
  const excluded = meta.excluded_periods.includes(state.period);

  const excludedNotice = document.getElementById('excluded-notice');
  const slidersEl = document.getElementById('sliders');
  const heatmapSection = document.getElementById('heatmap-section');
  const bprSection = document.getElementById('bpr-section');

  if (excluded) {
    excludedNotice.hidden = false;
    excludedNotice.textContent =
      `${meta.label} ${state.period}: excluded from calibration — congestion too infrequent ` +
      `to meet the eligibility threshold (density > 60 veh/mi/ln, ≥75 congested points per year ` +
      `of record). This is a result of the method, not missing data.`;
    slidersEl.hidden = true;
    heatmapSection.hidden = true;
    bprSection.hidden = true;
    return;
  }

  excludedNotice.hidden = true;
  slidersEl.hidden = false;
  heatmapSection.hidden = false;
  bprSection.hidden = false;

  const { facetResults, points, fit } = computeForCurrentSelection();
  renderHeatmap(facetResults);
  renderBpr(points, fit);
}

// ------------------------------------------------------------- heatmap --

function renderHeatmap(facetResults) {
  const cellSize = 6, cellGap = 1, rowGap = 22, leftPad = 34, topPad = 10;
  const maxWeeks = Math.max(...facetResults.map((f) =>
    f.segments.length ? f.segments[f.segments.length - 1].endObs : 0
  ), 1);
  const width = leftPad + maxWeeks * (cellSize + cellGap) + 10;
  const height = topPad + 7 * rowGap;

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', width);
  svg.setAttribute('height', height);

  let recurrentDays = 0, nonrecurrentDays = 0;

  facetResults.forEach((f, dow) => {
    const y = topPad + dow * rowGap;
    const label = document.createElementNS(svg.namespaceURI, 'text');
    label.setAttribute('x', 0);
    label.setAttribute('y', y + cellSize + 2);
    label.setAttribute('class', 'hm-label');
    label.textContent = DOW_NAMES[dow];
    svg.appendChild(label);

    f.segments.forEach((seg) => {
      const cls = seg.retained ? 'recurrent' : (seg.peakCount > 0 ? 'nonrecurrent' : 'none');
      if (seg.retained) recurrentDays += seg.peakCount;
      else nonrecurrentDays += seg.peakCount;
      for (let w = seg.startObs; w < seg.endObs; w++) {
        const rect = document.createElementNS(svg.namespaceURI, 'rect');
        rect.setAttribute('x', leftPad + w * (cellSize + cellGap));
        rect.setAttribute('y', y);
        rect.setAttribute('width', cellSize);
        rect.setAttribute('height', cellSize);
        rect.setAttribute('class', `hm-cell ${cls}`);
        svg.appendChild(rect);
      }
    });
  });

  const container = document.getElementById('heatmap');
  container.innerHTML = '';
  container.appendChild(svg);

  const total = recurrentDays + nonrecurrentDays;
  const pct = total > 0 ? Math.round((100 * recurrentDays) / total) : 0;
  document.getElementById('heatmap-stats').innerHTML =
    `<span><b>${pct}%</b> of congested days classified as recurrent</span>` +
    `<span><b>${recurrentDays}</b> recurrent days · <b>${nonrecurrentDays}</b> non-recurrent</span>`;
}

// ----------------------------------------------------------------- bpr --

function renderBpr(points, fit) {
  const w = 480, h = 320, pad = 44;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', w);
  svg.setAttribute('height', h);

  const container = document.getElementById('bpr-chart');
  container.innerHTML = '';
  const statsEl = document.getElementById('bpr-stats');

  if (!fit || points.length === 0) {
    container.appendChild(svg);
    statsEl.textContent = 'Not enough retained segments at these parameters to fit a curve.';
    return;
  }

  const xs = points.map((p) => p.lnN), ys = points.map((p) => p.lnTau);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys, fit.lnAlpha + fit.beta * xMin);
  const yMax = Math.max(...ys, fit.lnAlpha + fit.beta * xMax);
  const xPad = (xMax - xMin || 1) * 0.08, yPad = (yMax - yMin || 1) * 0.12;

  const sx = (x) => pad + ((x - (xMin - xPad)) / ((xMax + xPad) - (xMin - xPad))) * (w - 2 * pad);
  const sy = (y) => h - pad - ((y - (yMin - yPad)) / ((yMax + yPad) - (yMin - yPad))) * (h - 2 * pad);

  // axes
  const axisX = document.createElementNS(svg.namespaceURI, 'line');
  axisX.setAttribute('x1', pad); axisX.setAttribute('x2', w - pad);
  axisX.setAttribute('y1', h - pad); axisX.setAttribute('y2', h - pad);
  axisX.setAttribute('class', 'bpr-axis');
  svg.appendChild(axisX);
  const axisY = document.createElementNS(svg.namespaceURI, 'line');
  axisY.setAttribute('x1', pad); axisY.setAttribute('x2', pad);
  axisY.setAttribute('y1', pad); axisY.setAttribute('y2', h - pad);
  axisY.setAttribute('class', 'bpr-axis');
  svg.appendChild(axisY);

  const xLabel = document.createElementNS(svg.namespaceURI, 'text');
  xLabel.setAttribute('x', w / 2); xLabel.setAttribute('y', h - 10);
  xLabel.setAttribute('text-anchor', 'middle'); xLabel.setAttribute('class', 'bpr-axis-label');
  xLabel.textContent = 'ln(demand)';
  svg.appendChild(xLabel);
  const yLabel = document.createElementNS(svg.namespaceURI, 'text');
  yLabel.setAttribute('x', 14); yLabel.setAttribute('y', h / 2);
  yLabel.setAttribute('text-anchor', 'middle'); yLabel.setAttribute('class', 'bpr-axis-label');
  yLabel.setAttribute('transform', `rotate(-90 14 ${h / 2})`);
  yLabel.textContent = 'ln(z/ζ - 1)';
  svg.appendChild(yLabel);

  // fit line
  const path = document.createElementNS(svg.namespaceURI, 'path');
  const x1 = xMin - xPad, x2 = xMax + xPad;
  path.setAttribute('d', `M ${sx(x1)} ${sy(fit.lnAlpha + fit.beta * x1)} L ${sx(x2)} ${sy(fit.lnAlpha + fit.beta * x2)}`);
  path.setAttribute('class', 'bpr-fit-line');
  svg.appendChild(path);

  // points
  for (const p of points) {
    const c = document.createElementNS(svg.namespaceURI, 'circle');
    c.setAttribute('cx', sx(p.lnN));
    c.setAttribute('cy', sy(p.lnTau));
    c.setAttribute('r', 4);
    c.setAttribute('class', 'bpr-point live');
    svg.appendChild(c);
  }

  container.appendChild(svg);
  statsEl.innerHTML =
    `<span>N = <b>${fit.n}</b></span>` +
    `<span>β = <b>${fit.beta.toFixed(3)}</b></span>` +
    `<span>R² = <b>${fit.r2.toFixed(3)}</b></span>` +
    `<span>ln α̃ = <b>${fit.lnAlpha.toFixed(3)}</b></span>`;
}

// -------------------------------------------------------------- events --

function wireControls() {
  document.querySelectorAll('#period-toggle .toggle').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.period = btn.dataset.period;
      updatePeriodToggleUI();
      render();
    });
  });

  const epsSlider = document.getElementById('eps-slider');
  const epsValue = document.getElementById('eps-value');
  epsSlider.addEventListener('input', () => {
    state.eps = parseFloat(epsSlider.value);
    epsValue.textContent = `${state.eps.toFixed(2)} h`;
    render();
  });
  document.getElementById('eps-reset').addEventListener('click', () => {
    state.eps = state.period === 'AM' ? REF.AM : REF.PM;
    epsSlider.value = state.eps;
    epsValue.textContent = `${state.eps.toFixed(2)} h`;
    render();
  });

  const minLenSlider = document.getElementById('minlen-slider');
  const minLenValue = document.getElementById('minlen-value');
  minLenSlider.addEventListener('input', () => {
    state.minLen = parseInt(minLenSlider.value, 10);
    minLenValue.textContent = state.minLen;
    render();
  });
  document.getElementById('minlen-reset').addEventListener('click', () => {
    state.minLen = REF.minLen;
    minLenSlider.value = state.minLen;
    minLenValue.textContent = state.minLen;
    render();
  });
}

// ---------------------------------------------------------------- init --

(async function init() {
  state.manifest = await loadManifest();
  initMap(state.manifest);
  wireControls();
})();

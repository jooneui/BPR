/**
 * P3 — Full parity harness. Runs the JS port (rdpv.js + bpr.js) at the C3a
 * reference parameters across all 9 stations x 2 periods and compares
 * against references/bpr_calibration_reference_C3a.csv, the pipeline-
 * generated ground truth confirmed in Frame.
 *
 * This is the actual closure evidence for Frame's G1 and Plan's P3 phase.
 */
const fs = require('fs');
const path = require('path');
const { classifyFacetRdpv, computeWeekNums } = require('./rdpv.js');
const { calibrateStationPeriod } = require('./bpr.js');

const DATA_DIR = path.join(__dirname, '..', 'data');
const REF_CSV = path.join(__dirname, '..', 'references', 'bpr_calibration_reference_C3a.csv');

const EPS = { AM: 0.15, PM: 0.19 };
const MIN_LEN = 3;

function loadReference() {
  const lines = fs.readFileSync(REF_CSV, 'utf8').trim().split('\n');
  const rows = lines.slice(1).map((line) => {
    // simple CSV split -- no quoted commas in this file
    const cols = line.split(',');
    return {
      vds: cols[0], period: cols[1], n: parseInt(cols[2], 10),
      lnAlpha: cols[3] === '' ? null : parseFloat(cols[3]),
      beta: cols[7] === '' ? null : parseFloat(cols[7]),
    };
  });
  return rows;
}

function runStationPeriod(station, isAm) {
  const dp = station.daily_peaks;
  const weekNums = computeWeekNums(dp.date);
  const period = isAm ? 'morning-peak' : 'afternoon-peak';
  const eps = isAm ? EPS.AM : EPS.PM;

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
    facetResults.push(classifyFacetRdpv(facet, period, eps, eps, MIN_LEN));
  }

  return calibrateStationPeriod(facetResults, station.zeta_h_per_mi);
}

function main() {
  const manifest = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'manifest.json'), 'utf8'));
  const ref = loadReference();
  const TOL = 1e-3; // >=3 decimals per C3

  let allPass = true;
  const results = [];

  for (const s of manifest.stations) {
    const station = JSON.parse(fs.readFileSync(path.join(DATA_DIR, s.file), 'utf8'));
    for (const [key, isAm] of [['AM', true], ['PM', false]]) {
      const refRow = ref.find((r) => r.vds === s.label && r.period === key);
      const excluded = s.excluded_periods.includes(key);

      if (excluded) {
        const pass = refRow.n === 0;
        results.push({ label: s.label, period: key, status: pass ? 'EXCLUDED (matches ref)' : 'MISMATCH: ref has N>0' });
        if (!pass) allPass = false;
        continue;
      }

      const { points, fit } = runStationPeriod(station, isAm);
      if (!fit) {
        results.push({ label: s.label, period: key, status: `FAIL: no fit produced (${points.length} points)` });
        allPass = false;
        continue;
      }
      const nMatch = fit.n === refRow.n;
      const aMatch = Math.abs(fit.lnAlpha - refRow.lnAlpha) < TOL;
      const bMatch = Math.abs(fit.beta - refRow.beta) < TOL;
      const pass = nMatch && aMatch && bMatch;
      if (!pass) allPass = false;
      results.push({
        label: s.label, period: key,
        status: pass ? 'OK' : 'MISMATCH',
        detail: `N=${fit.n}(ref ${refRow.n}) lnA=${fit.lnAlpha.toFixed(6)}(ref ${refRow.lnAlpha.toFixed(6)}) beta=${fit.beta.toFixed(6)}(ref ${refRow.beta.toFixed(6)})`,
      });
    }
  }

  console.log('VDS          Period  Status                    Detail');
  for (const r of results) {
    console.log(`${r.label.padEnd(12)} ${r.period.padEnd(6)}  ${r.status.padEnd(24)}  ${r.detail || ''}`);
  }
  console.log(allPass ? '\nALL PASS' : '\nSOME FAILED — see above');
  process.exit(allPass ? 0 : 1);
}

main();

const fs = require('fs');
const path = require('path');
const { classifyFacetRdpv, computeWeekNums } = require('./rdpv.js');

const DOW_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function loadStation(vds) {
  const raw = fs.readFileSync(path.join(__dirname, '..', 'data', `${vds}.json`), 'utf8');
  return JSON.parse(raw);
}

function retainedCountForPeriod(station, isAm, epsStart, epsEnd, minLen) {
  const dp = station.daily_peaks;
  const n = dp.date.length;

  // week_num computed once across the WHOLE station record (both periods),
  // matching prepare_peak_table's global anchor.
  const weekNums = computeWeekNums(dp.date);

  const period = isAm ? 'morning-peak' : 'afternoon-peak';
  let totalRetained = 0;
  const perDow = {};

  for (let dow = 0; dow < 7; dow++) {
    const idx = [];
    for (let i = 0; i < n; i++) {
      if (dp.is_am[i] === isAm && dp.dow[i] === dow) idx.push(i);
    }
    const facet = {
      date: idx.map((i) => dp.date[i]),
      weeks: idx.map((i) => weekNums[i]),
      startHours: idx.map((i) => dp.start_h[i]),
      endHours: idx.map((i) => dp.end_h[i]),
    };
    const { segments } = classifyFacetRdpv(facet, period, epsStart, epsEnd, minLen);
    const retained = segments.filter((s) => s.retained).length;
    perDow[DOW_NAMES[dow]] = { qualifying: idx.length, retainedSegments: retained };
    totalRetained += retained;
  }
  return { totalRetained, perDow };
}

// C3a reference parameters
const EPS = { AM: 0.15, PM: 0.19 };
const MIN_LEN = 3;

const targets = [
  { vds: '1203506', label: 'SR91-EB', am: 19, pm: 13 },
  { vds: '1203481', label: 'SR91-WB', am: null, pm: 21 }, // AM excluded
  { vds: '1214006', label: 'I5 SB-1', am: 17, pm: null }, // PM excluded
  { vds: '1205572', label: 'I5 SB-2', am: 32, pm: null },
  { vds: '1212611', label: 'I5 SB-3', am: 29, pm: null },
  { vds: '1205175', label: 'I5 NB-1', am: null, pm: 21 },
  { vds: '774204',  label: 'SR134 WB-1', am: 14, pm: 27 },
  { vds: '761003',  label: 'SR134 EB-1', am: null, pm: 39 },
  { vds: '760987',  label: 'SR134 EB-2', am: null, pm: 10 },
];

console.log('VDS          Period  N(JS)  N(ref)  match');
let allMatch = true;
for (const t of targets) {
  const station = loadStation(t.vds);
  for (const [key, isAm] of [['am', true], ['pm', false]]) {
    const target = t[key];
    if (target === null) continue; // excluded periods handled separately (P0)
    const eps = key === 'am' ? EPS.AM : EPS.PM;
    const { totalRetained } = retainedCountForPeriod(station, isAm, eps, eps, MIN_LEN);
    const match = totalRetained === target;
    if (!match) allMatch = false;
    console.log(
      `${t.label.padEnd(12)} ${key.toUpperCase().padEnd(6)}  ${String(totalRetained).padEnd(5)}  ${String(target).padEnd(6)}  ${match ? 'OK' : 'MISMATCH'}`
    );
  }
}
console.log(allMatch ? '\nALL MATCH' : '\nSOME MISMATCH — see above');

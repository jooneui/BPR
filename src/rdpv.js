/**
 * Near-recurrent peak-period classification — JS port of
 * traffic_utils/segmentation.py::rdp_v and traffic_utils/recurrent.py::classify_facet_rdpv.
 *
 * Ported for the near-recurrent-explorer site (FPEV Stage-3 Execute, phase P1).
 * See ../handoffs/stage-3-phase-1-Sonnet5CC.md for verification.
 *
 * Only epsilon_start, epsilon_end, min_len are exposed as live parameters (Frame G3).
 * fixed_var and selector are NOT user-adjustable and are hardcoded to MASTER_CONFIG's
 * values below.
 */

// fixed_var_by_period from MASTER_CONFIG (not exposed to the user)
const FIXED_VAR_BY_PERIOD = { 'morning-peak': 'start_hour', 'afternoon-peak': 'end_hour' };
// selector_by_period from MASTER_CONFIG — always 'both' for this project
const SELECTOR = 'both';

/**
 * Modified RDP with vertical error, full recursion.
 * points: Array<[x:number, y:number]>, sorted by x.
 * Returns the kept points (first/last always included), preserving order.
 * Direct port of _rdp_vertical_recursive in segmentation.py.
 */
function rdpVertical(points, epsilon) {
  const n = points.length;
  if (n <= 2) return points;

  const [x1, y1] = points[0];
  const [x2, y2] = points[n - 1];
  const dx = x2 - x1;

  const yLine = new Array(n);
  if (dx === 0) {
    for (let i = 0; i < n; i++) yLine[i] = y1 + (i / (n - 1)) * (y2 - y1);
  } else {
    for (let i = 0; i < n; i++) {
      const t = (points[i][0] - x1) / dx;
      yLine[i] = y1 + t * (y2 - y1);
    }
  }

  let dmax = 0, idxMax = -1;
  // numpy argmax picks the FIRST occurrence of the max on ties; strict '>' here matches that.
  for (let i = 1; i < n - 1; i++) {
    const err = Math.abs(points[i][1] - yLine[i]);
    if (err > dmax) { dmax = err; idxMax = i; }
  }

  if (dmax > epsilon) {
    const left = rdpVertical(points.slice(0, idxMax + 1), epsilon);
    const right = rdpVertical(points.slice(idxMax), epsilon);
    return left.slice(0, -1).concat(right);
  }
  return [points[0], points[n - 1]];
}

/**
 * Direct port of _dedup_multiple_peaks (recurrent.py), default branch only
 * (drop_multiplecongestion_days=False, MASTER_CONFIG's setting — the only
 * mode this project needs). Keeps the longest-duration peak per date;
 * tie-break earliest start hour.
 *
 * Discovered necessary during phase-1 verification, not optional: the raw
 * Stage-1 CSVs carry genuine same-date duplicate (date, period) rows for
 * several stations (e.g. 4917 of 11465 rows for VDS 1203506, ~43%) — see
 * phase-1 handoff. Originally deprioritized as "probably not exercised";
 * it is, heavily, and its absence was the entire cause of the first
 * verification run's systematic undercount.
 *
 * rows: { date: number[], week: number[], startHour: number[], endHour: number[] }
 *   already filtered to one (dayofweek, period) facet, unsorted.
 */
function dedupMultiplePeaks(rows) {
  const n = rows.date.length;
  const byDate = new Map();
  for (let i = 0; i < n; i++) {
    const d = rows.date[i];
    const duration = rows.endHour[i] - rows.startHour[i];
    const candidate = { i, duration, startHour: rows.startHour[i] };
    const existing = byDate.get(d);
    if (
      !existing ||
      duration > existing.duration ||
      (duration === existing.duration && candidate.startHour < existing.startHour)
    ) {
      byDate.set(d, candidate);
    }
  }
  const keepIdx = [...byDate.values()].map((v) => v.i);
  // Carry any extra parallel arrays (P2 needs demand/traveltime alongside
  // weeks/hours) through dedup without duplicating the date/duration logic.
  const extraKeys = Object.keys(rows).filter(
    (k) => !['date', 'week', 'startHour', 'endHour'].includes(k)
  );
  const out = {
    date: keepIdx.map((i) => rows.date[i]),
    week: keepIdx.map((i) => rows.week[i]),
    startHour: keepIdx.map((i) => rows.startHour[i]),
    endHour: keepIdx.map((i) => rows.endHour[i]),
  };
  for (const k of extraKeys) out[k] = keepIdx.map((i) => rows[k][i]);
  return out;
}

/**
 * Classifies one (day-of-week, period) facet's qualifying weeks into
 * near-recurrent segments. Direct port of classify_facet_rdpv (Section 3 of
 * the paper), including the dedup step (Step 0 in the Python source).
 *
 * facet: { date: number[], weeks: number[], startHours: number[], endHours: number[] }
 *   Filtered to this station's qualifying rows for one (dayofweek, period)
 *   facet. Need not be pre-sorted or pre-deduped — both happen here.
 * period: 'morning-peak' | 'afternoon-peak'
 * epsStart, epsEnd: RDP vertical tolerances (site sliders)
 * minWeeks: segment_min_weeks (site slider, L in the paper)
 */
function classifyFacetRdpv(facet, period, epsStart, epsEnd, minWeeks) {
  const dedupInput = {
    date: facet.date, week: facet.weeks,
    startHour: facet.startHours, endHour: facet.endHours,
  };
  // P2 needs demand/traveltime carried through the same dedup+sort as the
  // RDP classification, so segments can be re-aggregated exactly.
  if (facet.demand) dedupInput.demand = facet.demand;
  if (facet.traveltime) dedupInput.traveltime = facet.traveltime;
  const deduped = dedupMultiplePeaks(dedupInput);
  // sort by week ascending — the qualifying-week subsequence order Python
  // relies on (out.sort_values('date_dt') upstream of peak_positions).
  const order = deduped.week.map((_, i) => i).sort((a, b) => deduped.week[a] - deduped.week[b]);
  const weeks = order.map((i) => deduped.week[i]);
  const startHours = order.map((i) => deduped.startHour[i]);
  const endHours = order.map((i) => deduped.endHour[i]);
  const demand = deduped.demand ? order.map((i) => deduped.demand[i]) : null;
  const traveltime = deduped.traveltime ? order.map((i) => deduped.traveltime[i]) : null;

  const N = weeks.length;
  if (N === 0) return { segments: [] };

  const shift = period === 'afternoon-peak' ? 12.0 : 0.0;
  const startShifted = startHours.map((h) => h - shift);
  const endShifted = endHours.map((h) => h - shift);

  const fixedVar = FIXED_VAR_BY_PERIOD[period];
  const epsPrimary = fixedVar === 'start_hour' ? epsStart : epsEnd;
  const epsSecondary = fixedVar === 'start_hour' ? epsEnd : epsStart;

  const x = Array.from({ length: N + 1 }, (_, i) => i);
  const S = [0]; for (let i = 0; i < N; i++) S.push(S[i] + startShifted[i]);
  const E = [0]; for (let i = 0; i < N; i++) E.push(E[i] + endShifted[i]);

  const zip = (xs, ys) => xs.map((xi, i) => [xi, ys[i]]);
  const ptsPrimary = fixedVar === 'start_hour' ? zip(x, S) : zip(x, E);
  const ptsSecondary = fixedVar === 'start_hour' ? zip(x, E) : zip(x, S);

  const interior = (pts, eps) =>
    rdpVertical(pts, eps)
      .map(([xi]) => xi)
      .filter((xi) => xi > 0 && xi < N)
      .sort((a, b) => a - b);

  // selector is always 'both' for this project (see SELECTOR above).
  const bpPrimary = interior(ptsPrimary, epsPrimary);
  const bpSecondary = interior(ptsSecondary, epsSecondary);
  const bpStart = fixedVar === 'start_hour' ? bpPrimary : bpSecondary;
  const bpEnd = fixedVar === 'start_hour' ? bpSecondary : bpPrimary;

  const gapPositions = [];
  for (let n = 1; n < N; n++) {
    if (weeks[n] - weeks[n - 1] > 1) gapPositions.push(n);
  }

  const allBkpts = [...new Set([...bpStart, ...bpEnd, ...gapPositions])].sort((a, b) => a - b);
  const boundaries = [0, ...allBkpts, N];

  const segments = [];
  for (let k = 0; k < boundaries.length - 1; k++) {
    const rStart = boundaries[k], rEnd = boundaries[k + 1];
    const segLen = rEnd - rStart;
    segments.push({
      startObs: rStart,
      endObs: rEnd,
      peakCount: segLen,
      retained: segLen >= minWeeks,
      weeks: weeks.slice(rStart, rEnd),
      startHours: startHours.slice(rStart, rEnd),
      endHours: endHours.slice(rStart, rEnd),
      demand: demand ? demand.slice(rStart, rEnd) : null,
      traveltime: traveltime ? traveltime.slice(rStart, rEnd) : null,
    });
  }

  return { segments, breakpointsStart: bpStart, breakpointsEnd: bpEnd, gapPositions };
}

/**
 * Builds calendar week_num for every row of a station's exported daily_peaks,
 * matching prepare_peak_table's construction: week_num is 1-indexed from the
 * Monday-week containing the EARLIEST date in the record, so gaps in the
 * calendar (weeks with zero detected peaks) still advance the index.
 *
 * Uncertainty (U-P1-2, see phase-1 handoff): Python's anchor date is the
 * earliest date across the station's FULL raw file (including off-peak-only
 * days), which this export does not carry (Frame D — off-peak rows dropped).
 * The anchor used here is the earliest date across this station's exported
 * congested-day rows instead. These differ only if the very first day(s) of
 * the study period had zero detected congestion in both AM and PM, which
 * would shift week_num by at most a few days at the very start of the
 * record. Flagged for the parity harness (P3) to catch if it matters.
 */
function computeWeekNums(dateInts) {
  // dateInts: array of YYMMDD integers (as exported: 'date' field).
  const toDate = (d) => {
    const s = String(d).padStart(6, '0');
    const yy = parseInt(s.slice(0, 2), 10);
    const mm = parseInt(s.slice(2, 4), 10) - 1;
    const dd = parseInt(s.slice(4, 6), 10);
    // PeMS dates are 2000s; matches pd.to_datetime's default century inference
    // for 2-digit years in this range.
    return new Date(Date.UTC(2000 + yy, mm, dd));
  };
  const dates = dateInts.map(toDate);
  const mondayOf = (d) => {
    const day = d.getUTCDay(); // 0=Sun..6=Sat
    const offset = day === 0 ? 6 : day - 1; // days since Monday
    const m = new Date(d);
    m.setUTCDate(m.getUTCDate() - offset);
    return m;
  };
  const mondays = dates.map(mondayOf);
  const minMonday = new Date(Math.min(...mondays.map((m) => m.getTime())));
  const MS_PER_DAY = 86400000;
  return mondays.map((m) => Math.floor((m - minMonday) / MS_PER_DAY / 7) + 1);
}

if (typeof module !== 'undefined') {
  module.exports = { rdpVertical, classifyFacetRdpv, computeWeekNums, dedupMultiplePeaks };
}

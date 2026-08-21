/**
 * BPR calibration — JS port of traffic_utils/bpr_fitting.py's
 * aggregate_segment_level_bpr (segment_aggregation branch) and
 * fit_bpr_ols_stats (T/R/I/C axes not relevant here; just the OLS fit).
 *
 * Ported for the near-recurrent-explorer site (FPEV Stage-3 Execute, phase P2).
 * See ../handoffs/stage-3-phase-2-Sonnet5CC.md for verification.
 *
 * IMPORTANT — replicated faithfully, not "fixed": bpr_fitting.py's
 * weighted_harmonic_mean(values, weights) computes sum(weights*values)/sum(weights)
 * -- a weighted ARITHMETIC mean of `values`, despite the function's name. The
 * paper's Eq. 9 describes an N_j-weighted harmonic mean of speed. This port
 * matches what the CODE does (since C3 requires matching the confirmed
 * pipeline output), not what the paper's prose describes. Flagged as a
 * paper/code discrepancy in the phase-2 handoff, same spirit as Frame's G11 --
 * not something this project corrects.
 */

/**
 * Aggregates one retained segment's member days into one (N_r, z_r)
 * observation. segment: output of classifyFacetRdpv's segments[], with
 * demand/traveltime arrays attached.
 * zeta: this station's free-flow travel time (h/mi), i.e. free_traveltime.
 * Returns null if the segment doesn't produce a usable point (matches
 * Python's tau_ratio <= 0 / avg_demand <= 0 exclusion).
 */
function aggregateSegment(segment, zeta) {
  const { demand, traveltime } = segment;
  if (!demand || !traveltime || demand.length === 0) return null;

  // avg_demand: arithmetic mean of totaldemandoverlanes (Eq. 9's N_r).
  const avgDemand = demand.reduce((a, b) => a + b, 0) / demand.length;

  // avg_tt: weighted_harmonic_mean(traveltimes, totaldemandoverlanes) as
  // actually implemented -- sum(w*v)/sum(w), weights = demand. See module
  // docstring: this is a weighted arithmetic mean of traveltime, not the
  // harmonic mean of speed the paper's prose describes.
  let wSum = 0, wvSum = 0;
  for (let i = 0; i < demand.length; i++) {
    const w = demand[i], v = traveltime[i];
    if (!(Number.isFinite(w) && Number.isFinite(v) && w > 0 && v > 0)) continue;
    wSum += w;
    wvSum += w * v;
  }
  const avgTt = wSum > 0 ? wvSum / wSum : NaN;

  if (!(avgDemand > 0) || !Number.isFinite(avgTt) || !(zeta > 0)) return null;
  const tauRatio = avgTt / zeta - 1.0;
  if (!(tauRatio > 0)) return null;

  return { N: avgDemand, lnN: Math.log(avgDemand), lnTau: Math.log(tauRatio) };
}

/**
 * Ordinary least squares, y = a + b*x, matching fit_bpr_ols_stats's use of
 * statsmodels.OLS (a = ln_tilde_alpha, b = beta). Returns null if fewer than
 * 5 points or all x equal (matches Python's early-return conditions).
 */
function olsFit(points) {
  const n = points.length;
  if (n < 5) return null;
  const xs = points.map((p) => p.lnN);
  const ys = points.map((p) => p.lnTau);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  if (xMax === xMin) return null;

  const xMean = xs.reduce((a, b) => a + b, 0) / n;
  const yMean = ys.reduce((a, b) => a + b, 0) / n;
  let sXY = 0, sXX = 0;
  for (let i = 0; i < n; i++) {
    sXY += (xs[i] - xMean) * (ys[i] - yMean);
    sXX += (xs[i] - xMean) * (xs[i] - xMean);
  }
  const beta = sXY / sXX;
  const lnAlpha = yMean - beta * xMean;

  // R^2
  let ssRes = 0, ssTot = 0;
  for (let i = 0; i < n; i++) {
    const yHat = lnAlpha + beta * xs[i];
    ssRes += (ys[i] - yHat) ** 2;
    ssTot += (ys[i] - yMean) ** 2;
  }
  const r2 = ssTot > 0 ? 1 - ssRes / ssTot : NaN;

  return { n, lnAlpha, beta, r2 };
}

/**
 * Full station-period calibration: takes classifyFacetRdpv results for all
 * 7 day-of-week facets (already run at the live epsilon/minWeeks parameters)
 * and this station's zeta; returns the fit, or null if ineligible/no points.
 */
function calibrateStationPeriod(facetResultsByDow, zeta) {
  const points = [];
  for (const { segments } of facetResultsByDow) {
    for (const seg of segments) {
      if (!seg.retained) continue;
      const p = aggregateSegment(seg, zeta);
      if (p) points.push(p);
    }
  }
  const fit = olsFit(points);
  return { points, fit };
}

if (typeof module !== 'undefined') {
  module.exports = { aggregateSegment, olsFit, calibrateStationPeriod };
}

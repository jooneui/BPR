# PeakAtlas California

Static website starter for presenting a California traffic peak-period product.

## Files

- `index.html`: main product website
- `styles.css`: design and layout
- `site-data.js`: generated station summaries used by the site
- `app.js`: interactive explorer logic
- `scripts/generate_site_data.py`: rebuilds `site-data.js` from your peak output CSV files

## Open locally

You can open `index.html` directly in a browser.

If you want to run a local server:

```bash
cd peak-atlas-site
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

## Publish with GitHub Pages

For this repo, the simplest publish path is GitHub Pages from the `docs/` folder.

### One-time GitHub setup

1. Push the workflow and site files to `main`.
2. In GitHub, open `Settings` -> `Pages`.
3. Under `Build and deployment`, set `Source` to `Deploy from a branch`.
4. Select branch `main` and folder `/docs`.
5. Save. GitHub will publish the static files inside `docs/`.

### Recommended push commands for this repo

Because your repo already has unrelated modified files, stage only the website and workflow files:

```bash
cd "/Users/jooneuihong/Library/CloudStorage/OneDrive-UCIrvine/14 Github"
git add -f peak-atlas-site docs
git commit -m "Add PeakAtlas California site"
git push origin main
```

## Refresh the data

Rebuild the site data whenever you have updated peak-period outputs:

```bash
cd peak-atlas-site
python3 scripts/generate_site_data.py
```

The current generator reads:

- `01_BPR/c_daily_traffic_segment_single_*speedbasedpeak_5_RDP_v_speed-solely.csv`

It creates station-year summaries with:

- AM median peak start time and duration
- PM median peak start time and duration
- AM coverage and PM coverage
- simple story labels for the website

## Current data note

The connected real-data pilot currently uses the station-year outputs already present in the workspace.
At the moment, the files provide 2011 results for some stations and 2024 results for others, so the website is now a real station-based pilot rather than a full statewide year-over-year comparison.

## Suggested future additions

- county-level California map
- downloadable charts
- method/data page with your exact study description
- links to paper, thesis, or report

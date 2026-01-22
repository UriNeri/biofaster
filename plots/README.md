# GitHub Pages - Benchmark Results

The `plots/` directory contains all visualization files and serves as the root for GitHub Pages.

## Publishing Results

### Option 1: Manual Trigger
1. Go to Actions tab in GitHub
2. Select "Publish Benchmark Results" workflow
3. Click "Run workflow"

### Option 2: Automatic (when plots change)
The workflow automatically triggers when files in `plots/` or `benchmark_results/` are pushed.

## What Gets Published

- All HTML chart files from `plots/`
- Latest benchmark markdown reports (hot_raw.md, etc.)
- benchmark_summary.csv
- SUMMARY.txt

## Setup GitHub Pages

1. Go to Settings → Pages
2. Source: GitHub Actions
3. The workflow will handle the rest

## Local Preview

Open `plots/index.html` in your browser to preview locally before publishing.

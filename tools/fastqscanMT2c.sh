#!/bin/bash
# fastqscan: BBTools' ultra-fast parser (skips validation & object allocation)
# Args: $1 = input FASTQ file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi

# Set BBTools path - use environment variable or default
BBTOOLS_PATH="${BBTOOLS_PATH:-$BIOFASTER_ROOT/BBTools/current/}"
BBTOOLS_BASE=$(dirname "$BBTOOLS_PATH")
THREADS=2
if [ ! -f "$BBTOOLS_BASE/fastqscan.sh" ]; then
    echo "Error: fastqscan not found at $BBTOOLS_BASE/fastqscan.sh" >&2
    echo "Set BBTOOLS_PATH environment variable or install BBTools" >&2
    exit 1
fi

exec "$BBTOOLS_BASE/fastqscan.sh" "$1" t=2 bgzfthreadsin=2


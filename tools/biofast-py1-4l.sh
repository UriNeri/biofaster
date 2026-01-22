#!/bin/bash
# biofast-py1-4l: Pure Python implementation (4-line FASTQ parser)
# Args: $1 = input FASTQ file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi

PYTHON_SCRIPT="$BIOFASTER_ROOT/biofast-reference/fqcnt/fqcnt_py1_4l.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

exec pixi run python "$PYTHON_SCRIPT" "$1"

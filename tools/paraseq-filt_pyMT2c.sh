#!/bin/bash
# needletail-python: Python bindings to needletail (tests FFI overhead)
# Args: $1 = input FASTQ file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi
threads=2
PYTHON_SCRIPT="$BIOFASTER_ROOT/src/paraseq_filt_py.py"

# Check if script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

exec pixi run python "$PYTHON_SCRIPT" "$1" "$threads"

#!/bin/bash
# biofast-py7-pysam: Python with pysam library (samtools bindings)
# Args: $1 = input FASTQ file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi

PYTHON_SCRIPT="$BIOFASTER_ROOT/biofast-reference/fqcnt/fqcnt_py7x_pysam.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Check if pysam is installed
if ! pixi run python -c "import pysam" 2>/dev/null; then
    echo "Error: pysam not installed. Install with: pixi add pysam" >&2
    exit 1
fi

exec pixi run python "$PYTHON_SCRIPT" "$1"

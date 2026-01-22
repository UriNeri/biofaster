#!/bin/bash
# biofast-py6-pyfx: Python with pyfastx library
# Args: $1 = input FASTQ file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi

PYTHON_SCRIPT="$BIOFASTER_ROOT/biofast-reference/fqcnt/fqcnt_py6x_pyfx.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Check if pyfastx is installed
if ! pixi run python -c "import pyfastx" 2>/dev/null; then
    echo "Error: pyfastx not installed. Install with: pixi add pyfastx" >&2
    exit 1
fi

exec pixi run python "$PYTHON_SCRIPT" "$1"

#!/bin/bash
# biofast-py3-mappy: Python with mappy library (minimap2 bindings)
# Args: $1 = input FASTQ file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi

PYTHON_SCRIPT="$BIOFASTER_ROOT/biofast-reference/fqcnt/fqcnt_py3x_mappy.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Check if mappy is installed
if ! pixi run python -c "import mappy" 2>/dev/null; then
    echo "Error: mappy not installed. Install with: pixi add mappy --pypi" >&2
    exit 1
fi

exec pixi run python "$PYTHON_SCRIPT" "$1"

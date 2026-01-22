#!/bin/bash
# biofast-py5-bp: Python with BioPython SeqIO.parse
# Args: $1 = input FASTQ file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi

PYTHON_SCRIPT="$BIOFASTER_ROOT/biofast-reference/fqcnt/fqcnt_py5x_bp.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Check if BioPython is installed
if ! pixi run python -c "from Bio import SeqIO" 2>/dev/null; then
    echo "Error: BioPython not installed. Install with: pixi add biopython" >&2
    exit 1
fi

exec pixi run python "$PYTHON_SCRIPT" "$1"

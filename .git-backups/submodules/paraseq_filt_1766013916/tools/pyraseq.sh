#!/bin/bash
# pyraseq - Python wrapper for paraseq_filt counting
# This tool uses the Python bindings for biofaster compatibility

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <input.fasta[.gz]>" >&2
    exit 1
fi

INPUT_FILE="$1"

# Find Python with paraseq_filt installed
# Assumes this script is in tools/ and project root has .pixi or venv
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Try pixi environment first
if [[ -f "$PROJECT_ROOT/pixi.toml" ]]; then
    cd "$PROJECT_ROOT"
    exec pixi run python -c "import paraseq_filt; n_seqs, n_bases = paraseq_filt.count_records('$INPUT_FILE'); print(f'{n_seqs}\t{n_bases}')" 2>/dev/null
fi

# Try direct Python import (if installed in system/venv)
exec python3 -c "import paraseq_filt; n_seqs, n_bases = paraseq_filt.count_records('$INPUT_FILE'); print(f'{n_seqs}\t{n_bases}')" 2>/dev/null

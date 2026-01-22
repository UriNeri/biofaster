#!/bin/bash
# paraseq-filt: Parallel FASTA/FASTQ parser using paraseq (Rust)
# Args: $1 = input FASTQ/FASTA file path

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
PARASEQ_BIN="$SCRIPT_DIR/target/release/paraseq_filt"

# Check if binary exists
if [ ! -f "$PARASEQ_BIN" ]; then
    echo "Error: paraseq_filt binary not found at $PARASEQ_BIN" >&2
    echo "Run: cargo build --release" >&2
    exit 1
fi

# Use count mode for benchmarking - just counts reads and bases
exec "$PARASEQ_BIN" --count -i "$1" 2>/dev/null

#!/bin/bash
# paraseq-filt: Parallel FASTA/FASTQ parser using paraseq (Rust)
# Args: $1 = input FASTQ/FASTA file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi

PARASEQ_BIN="$BIOFASTER_ROOT/paraseq_filt/target/release/paraseq_filt"
THREADS=2
# Check if binary exists
if [ ! -f "$PARASEQ_BIN" ]; then
    echo "Error: paraseq_filt binary not found at $PARASEQ_BIN" >&2
    echo "Run: cargo build --release" >&2
    exit 1
fi

# Use count mode for benchmarking - just counts reads and bases
exec "$PARASEQ_BIN" --count --threads "$THREADS" -i "$1" 2>/dev/null

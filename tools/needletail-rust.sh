#!/bin/bash
# needletail-rust: Fast Rust-based FASTQ parser with SIMD base counting
# Args: $1 = input FASTQ file path

if [ -z "$BIOFASTER_ROOT" ]; then
    echo "Error: BIOFASTER_ROOT not set. Run from run_all_benchmarks.sh" >&2
    exit 1
fi

NEEDLETAIL_BIN="$BIOFASTER_ROOT/target/release/fqcnt_nt"

# Check if binary exists
if [ ! -f "$NEEDLETAIL_BIN" ]; then
    echo "Error: needletail binary not found at $NEEDLETAIL_BIN" >&2
    echo "Run: cargo build --release" >&2
    exit 1
fi

exec "$NEEDLETAIL_BIN" "$1"

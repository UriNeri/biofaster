#!/bin/bash
# Benchmark paraseq_filt vs seqkit grep

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "  Benchmark: paraseq_filt vs seqkit grep"
echo "=================================================="
echo ""

# Check if seqkit is available
if ! command -v seqkit &> /dev/null; then
    echo "Error: seqkit not found. Please install it first:"
    echo "  conda install -c bioconda seqkit"
    echo "  or"
    echo "  brew install seqkit"
    exit 1
fi

# Check if our binary exists
if [ ! -f "./target/release/paraseq_filt" ]; then
    echo "Building paraseq_filt..."
    cargo build --release
fi

# Create temp directory
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "Test directory: $TMPDIR"
echo ""

# Function to create test FASTA
create_fasta() {
    local file=$1
    local num_seqs=$2
    local seq_length=${3:-100}
    
    echo "  Creating test file with ${num_seqs} sequences..."
    
    # Simple Python-based FASTA generator
    python3 << EOF
import random
import sys

num_seqs = ${num_seqs}
seq_length = ${seq_length}

random.seed(42)
bases = ['A', 'C', 'G', 'T']

with open('${file}', 'w') as f:
    for i in range(1, num_seqs + 1):
        seq = ''.join(random.choices(bases, k=seq_length))
        f.write(f'>seq{i}\n{seq}\n')
EOF
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create test file"
        exit 1
    fi
}

# Function to run benchmark
run_benchmark() {
    local name=$1
    local num_seqs=$2
    local num_keep=$3
    local threads=$4
    
    echo -e "${BLUE}=== Test: ${name} ===${NC}"
    echo "  Sequences: ${num_seqs}, Keep: ${num_keep}, Threads: ${threads}"
    
    local input_file="$TMPDIR/test_${num_seqs}.fasta"
    local headers_file="$TMPDIR/headers_${num_keep}.txt"
    local output_paraseq="$TMPDIR/output_paraseq.fasta"
    local output_seqkit="$TMPDIR/output_seqkit.fasta"
    
    # Create test data if needed
    if [ ! -f "$input_file" ]; then
        create_fasta "$input_file" $num_seqs
    fi
    
    # Create headers file - keep every Nth sequence
    local step=$((num_seqs / num_keep))
    seq 1 $step $num_seqs | while read i; do echo "seq${i}"; done > "$headers_file"
    
    # Benchmark paraseq_filt
    echo -e "${YELLOW}  paraseq_filt:${NC}"
    local start=$(date +%s.%N)
    if ! ./target/release/paraseq_filt \
        -i "$input_file" \
        -o "$output_paraseq" \
        -H "$headers_file" \
        -t $threads \
        2>&1 | grep -v "^Using"; then
        echo "    Error: paraseq_filt failed"
        return 1
    fi
    local end=$(date +%s.%N)
    local time_paraseq=$(echo "$end - $start" | bc)
    local count_paraseq=$(grep -c "^>" "$output_paraseq" || true)
    echo "    Time: ${time_paraseq}s"
    echo "    Output: ${count_paraseq} sequences"
    
    # Benchmark seqkit grep
    echo -e "${YELLOW}  seqkit grep:${NC}"
    local start=$(date +%s.%N)
    if ! seqkit grep \
        -f "$headers_file" \
        -j $threads \
        "$input_file" \
        > "$output_seqkit" 2>&1; then
        echo "    Error: seqkit failed"
        return 1
    fi
    local end=$(date +%s.%N)
    local time_seqkit=$(echo "$end - $start" | bc)
    local count_seqkit=$(grep -c "^>" "$output_seqkit" || true)
    echo "    Time: ${time_seqkit}s"
    echo "    Output: ${count_seqkit} sequences"
    
    # Compare results
    if [ "$count_paraseq" -ne "$count_seqkit" ]; then
        echo -e "  ${YELLOW}Warning: Output counts differ!${NC}"
    fi
    
    # Calculate speedup
    local speedup=$(echo "scale=2; $time_seqkit / $time_paraseq" | bc)
    echo -e "  ${GREEN}Speedup: ${speedup}x${NC}"
    
    # Throughput
    local throughput_paraseq=$(echo "scale=0; $num_seqs / $time_paraseq" | bc)
    local throughput_seqkit=$(echo "scale=0; $num_seqs / $time_seqkit" | bc)
    echo "  Throughput:"
    echo "    paraseq_filt: ${throughput_paraseq} seq/s"
    echo "    seqkit:       ${throughput_seqkit} seq/s"
    echo ""
}

# Run benchmarks with different sizes and thread counts
echo "=================================================="
echo "Small file (10K sequences, keep 1K)"
echo "=================================================="
run_benchmark "Small-1thread" 10000 1000 1
run_benchmark "Small-4threads" 10000 1000 4
run_benchmark "Small-8threads" 10000 1000 8

echo "=================================================="
echo "Medium file (100K sequences, keep 10K)"
echo "=================================================="
run_benchmark "Medium-1thread" 100000 10000 1
run_benchmark "Medium-4threads" 100000 10000 4
run_benchmark "Medium-8threads" 100000 10000 8

echo "=================================================="
echo "Large file (1M sequences, keep 100K)"
echo "=================================================="
run_benchmark "Large-1thread" 1000000 100000 1
run_benchmark "Large-4threads" 1000000 100000 4
run_benchmark "Large-8threads" 1000000 100000 8
run_benchmark "Large-16threads" 1000000 100000 16


echo "=================================================="
echo "Larger file (10M sequences, keep 100K)"
echo "=================================================="
run_benchmark "Larger-1thread" 10000000 100000 1
run_benchmark "Larger-4threads" 10000000 100000 4
run_benchmark "Larger-8threads" 10000000 100000 8
run_benchmark "Largee-16threads" 10000000 100000 16

echo "=================================================="
echo "Test: Invert mode (exclude sequences)"
echo "=================================================="
echo ""

input_file="$TMPDIR/test_100000.fasta"
headers_file="$TMPDIR/headers_exclude.txt"
seq 1 10 50000 | while read i; do echo "seq${i}"; done > "$headers_file"

echo -e "${YELLOW}paraseq_filt --invert:${NC}"
start=$(date +%s.%N)
./target/release/paraseq_filt \
    -i "$input_file" \
    -o "$TMPDIR/out_paraseq_inv.fasta" \
    -H "$headers_file" \
    -t 8 \
    --invert \
    2>/dev/null
end=$(date +%s.%N)
time_paraseq=$(echo "$end - $start" | bc)
count_paraseq=$(grep -c "^>" "$TMPDIR/out_paraseq_inv.fasta" || true)
echo "  Time: ${time_paraseq}s"
echo "  Output: ${count_paraseq} sequences"

echo -e "${YELLOW}seqkit grep --invert-match:${NC}"
start=$(date +%s.%N)
seqkit grep \
    -f "$headers_file" \
    -j 8 \
    --invert-match \
    "$input_file" \
    > "$TMPDIR/out_seqkit_inv.fasta" 2>/dev/null
end=$(date +%s.%N)
time_seqkit=$(echo "$end - $start" | bc)
count_seqkit=$(grep -c "^>" "$TMPDIR/out_seqkit_inv.fasta" || true)
echo "  Time: ${time_seqkit}s"
echo "  Output: ${count_seqkit} sequences"

speedup=$(echo "scale=2; $time_seqkit / $time_paraseq" | bc)
echo -e "${GREEN}Speedup: ${speedup}x${NC}"

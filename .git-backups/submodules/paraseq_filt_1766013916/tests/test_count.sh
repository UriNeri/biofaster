#!/bin/bash
# Test count mode functionality

set -e

echo "Testing count mode..."

# Create temp dir
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create test FASTA
cat > "$TEMP_DIR/test.fasta" << 'EOF'
>seq1
ACGTACGT
>seq2
TGCATGCA
>seq3
AAAAAAAAAA
EOF

# Run count mode
RESULT=$(./target/release/paraseq_filt --count -i "$TEMP_DIR/test.fasta" 2>/dev/null)

# Check output format (should be: n_seqs\tn_bases)
echo "Result: $RESULT"

N_SEQS=$(echo "$RESULT" | cut -f1)
N_BASES=$(echo "$RESULT" | cut -f2)

if [ "$N_SEQS" != "3" ]; then
    echo "❌ Expected 3 sequences, got $N_SEQS"
    exit 1
fi

if [ "$N_BASES" != "26" ]; then
    echo "❌ Expected 26 bases, got $N_BASES"
    exit 1
fi

echo "✓ Count mode works correctly (3 sequences, 26 bases)"

# Test with gzipped file
gzip -c "$TEMP_DIR/test.fasta" > "$TEMP_DIR/test.fasta.gz"
RESULT_GZ=$(./target/release/paraseq_filt --count -i "$TEMP_DIR/test.fasta.gz" 2>/dev/null)

if [ "$RESULT_GZ" != "$RESULT" ]; then
    echo "❌ Gzipped count differs from raw count"
    echo "  Raw: $RESULT"
    echo "  Gzipped: $RESULT_GZ"
    exit 1
fi

echo "✓ Count mode works with gzipped input"

echo ""
echo "All count mode tests passed!"

#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Binary path
BINARY="./target/release/paraseq_filt"

# Temp directory for test files
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

echo "Running tests in: $TEST_DIR"
echo "================================"

# Helper function to run a test
run_test() {
    local test_name="$1"
    local expected_output="$2"
    local actual_output="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ "$expected_output" == "$actual_output" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected:"
        echo "$expected_output" | sed 's/^/    /'
        echo "  Got:"
        echo "$actual_output" | sed 's/^/    /'
    fi
}

# Helper function to compare files (handles unordered FASTA records from parallel processing)
compare_files() {
    local test_name="$1"
    local expected_file="$2"
    local actual_file="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    # Sort both files by header to handle unordered output from parallel processing
    local expected_sorted=$(mktemp)
    local actual_sorted=$(mktemp)
    
    # Extract headers and sequences, sort by header, then reconstruct
    awk '/^>/ {if (seq) print header"\n"seq; header=$0; seq=""; next} {seq=seq$0} END {if (seq) print header"\n"seq}' "$expected_file" | sort > "$expected_sorted"
    awk '/^>/ {if (seq) print header"\n"seq; header=$0; seq=""; next} {seq=seq$0} END {if (seq) print header"\n"seq}' "$actual_file" | sort > "$actual_sorted"
    
    if diff -q "$expected_sorted" "$actual_sorted" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Files differ:"
        diff "$expected_sorted" "$actual_sorted" | sed 's/^/    /'
    fi
    
    rm -f "$expected_sorted" "$actual_sorted"
}

# Create test FASTA file
cat > "$TEST_DIR/test.fasta" << 'EOF'
>seq1
ATCGATCGATCG
>seq2
GCTAGCTAGCTA
>seq3
TTTTAAAACCCC
>seq4
GGGGCCCCAAAA
>seq5
NNNNNNNNNNNN
EOF

# Create headers files
echo -e "seq1\nseq3\nseq5" > "$TEST_DIR/keep.txt"
echo -e "seq2\nseq4" > "$TEST_DIR/exclude.txt"

# Expected outputs
cat > "$TEST_DIR/expected_keep.fasta" << 'EOF'
>seq1
ATCGATCGATCG
>seq3
TTTTAAAACCCC
>seq5
NNNNNNNNNNNN
EOF

cat > "$TEST_DIR/expected_exclude.fasta" << 'EOF'
>seq2
GCTAGCTAGCTA
>seq4
GGGGCCCCAAAA
EOF

cat > "$TEST_DIR/expected_invert_keep.fasta" << 'EOF'
>seq2
GCTAGCTAGCTA
>seq4
GGGGCCCCAAAA
EOF

cat > "$TEST_DIR/expected_invert_exclude.fasta" << 'EOF'
>seq1
ATCGATCGATCG
>seq3
TTTTAAAACCCC
>seq5
NNNNNNNNNNNN
EOF

echo ""
echo "Test 1: Filter with headers from file"
$BINARY -i "$TEST_DIR/test.fasta" -o "$TEST_DIR/output1.fasta" -H "$TEST_DIR/keep.txt" 2>/dev/null
compare_files "Keep seq1, seq3, seq5 from file" "$TEST_DIR/expected_keep.fasta" "$TEST_DIR/output1.fasta"

echo ""
echo "Test 2: Filter with comma-separated headers"
$BINARY -i "$TEST_DIR/test.fasta" -o "$TEST_DIR/output2.fasta" -H "seq1,seq3,seq5" 2>/dev/null
compare_files "Keep seq1, seq3, seq5 from CLI" "$TEST_DIR/expected_keep.fasta" "$TEST_DIR/output2.fasta"

echo ""
echo "Test 3: Invert filter (exclude headers from file)"
$BINARY -i "$TEST_DIR/test.fasta" -o "$TEST_DIR/output3.fasta" -H "$TEST_DIR/keep.txt" --invert 2>/dev/null
compare_files "Exclude seq1, seq3, seq5" "$TEST_DIR/expected_invert_keep.fasta" "$TEST_DIR/output3.fasta"

echo ""
echo "Test 4: Invert filter with comma-separated headers"
$BINARY -i "$TEST_DIR/test.fasta" -o "$TEST_DIR/output4.fasta" -H "seq2,seq4" --invert 2>/dev/null
compare_files "Exclude seq2, seq4" "$TEST_DIR/expected_invert_exclude.fasta" "$TEST_DIR/output4.fasta"

echo ""
echo "Test 5: Filter with gzipped input"
gzip -c "$TEST_DIR/test.fasta" > "$TEST_DIR/test.fasta.gz"
$BINARY -i "$TEST_DIR/test.fasta.gz" -o "$TEST_DIR/output5.fasta" -H "seq1,seq3,seq5" 2>/dev/null
compare_files "Gzipped input" "$TEST_DIR/expected_keep.fasta" "$TEST_DIR/output5.fasta"

echo ""
echo "Test 6: Output to stdout"
ACTUAL_STDOUT=$($BINARY -i "$TEST_DIR/test.fasta" -o - -H "seq1,seq3,seq5" 2>/dev/null)
EXPECTED_STDOUT=$(cat "$TEST_DIR/expected_keep.fasta")
run_test "Stdout output" "$EXPECTED_STDOUT" "$ACTUAL_STDOUT"

echo ""
echo "Test 7: Empty headers list"
$BINARY -i "$TEST_DIR/test.fasta" -o "$TEST_DIR/output7.fasta" -H "nonexistent1,nonexistent2" 2>/dev/null
ACTUAL_COUNT=$(wc -l < "$TEST_DIR/output7.fasta")
TESTS_RUN=$((TESTS_RUN + 1))
if [ "$ACTUAL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Empty output for non-matching headers"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Empty output for non-matching headers"
    echo "  Expected 0 lines, got $ACTUAL_COUNT"
fi

echo ""
echo "Test 8: Invert with empty headers (should output all)"
$BINARY -i "$TEST_DIR/test.fasta" -o "$TEST_DIR/output8.fasta" -H "nonexistent" --invert 2>/dev/null
ACTUAL_COUNT=$(grep -c "^>" "$TEST_DIR/output8.fasta")
TESTS_RUN=$((TESTS_RUN + 1))
if [ "$ACTUAL_COUNT" -eq 5 ]; then
    echo -e "${GREEN}✓${NC} Invert with non-matching headers outputs all"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Invert with non-matching headers outputs all"
    echo "  Expected 5 records, got $ACTUAL_COUNT"
fi

echo ""
echo "Test 9: Multi-line FASTA"
cat > "$TEST_DIR/multiline.fasta" << 'EOF'
>seq1
ATCGATCG
ATCGATCG
>seq2
GCTAGCTA
GCTAGCTA
>seq3
TTTTAAAA
CCCCGGGG
EOF

cat > "$TEST_DIR/expected_multiline.fasta" << 'EOF'
>seq1
ATCGATCGATCGATCG
>seq3
TTTTAAAACCCCGGGG
EOF

$BINARY -i "$TEST_DIR/multiline.fasta" -o "$TEST_DIR/output9.fasta" -H "seq1,seq3" 2>/dev/null
compare_files "Multi-line FASTA" "$TEST_DIR/expected_multiline.fasta" "$TEST_DIR/output9.fasta"

echo ""
echo "Test 10: Thread count option"
cat > "$TEST_DIR/expected_subset.fasta" << 'EOF'
>seq1
ATCGATCGATCG
>seq3
TTTTAAAACCCC
EOF
$BINARY -i "$TEST_DIR/test.fasta" -o "$TEST_DIR/output10.fasta" -H "seq1,seq3" -t 4 2>/dev/null
compare_files "Custom thread count" "$TEST_DIR/expected_subset.fasta" "$TEST_DIR/output10.fasta"

echo ""
echo "================================"
echo "Tests run: $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    FAILED=$((TESTS_RUN - TESTS_PASSED))
    echo -e "${RED}Tests failed: $FAILED${NC}"
    exit 1
fi

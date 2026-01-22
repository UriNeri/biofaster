# Create data directory
DATA_DIR="test-data"
mkdir -p "$DATA_DIR"

# Generate test data files
echo ""
echo "Generating FASTQ test files..."
GENOME_FILE="$DATA_DIR/ref_genome.fa"

# BBTools/randomreadsmg.sh
BBTOOLS_DIR="BBTools/"
# Generate a reference genome (100kb, good for test data)
echo "Generating reference genome..."
"$BBTOOLS_DIR/randomgenome.sh" len=100000 seed=42 out="$GENOME_FILE" 2>/dev/null

# Define test sizes (in millions of reads)
declare -a SIZES=("0.1" "0.5" "1" "10" "30" "50" "70")

# Function to generate FASTQ files for a given size
generate_fastq_set() {
    local size_m=$1
    local num_reads=$(echo "$size_m * 1000000" | bc | cut -d. -f1)
    local size_label="${size_m}m"
    
    local raw_fq="$DATA_DIR/${size_label}.fastq"
    local gz_fq="$DATA_DIR/${size_label}.fastq.gz"
    local bgz_fq="$DATA_DIR/${size_label}.fastq_bgzipped.gz"
    
    echo ""
    echo "Generating ${size_label} reads files..."
    
    # Generate raw FASTQ (uncompressed)
    echo "  Creating raw FASTQ..."
        "$BBTOOLS_DIR/randomreadsmg.sh" \
            ref="$GENOME_FILE" \
            out="$raw_fq" \
            reads="$num_reads" \
            length=150 \
            seed=42 
            # 2>/dev/null
    echo "    ✓ $raw_fq ($(du -h "$raw_fq" | cut -f1))"

    
    # Generate standard gzipped FASTQ (compress externally with gzip)
        echo "  Creating gzipped FASTQ..."
        if command -v pigz &> /dev/null; then
            pigz -k -c "$raw_fq" > "$gz_fq"
        else
            gzip -k -c "$raw_fq" > "$gz_fq"
        fi
        echo "    ✓ $gz_fq ($(du -h "$gz_fq" | cut -f1))"

    
    # Generate bgzipped FASTQ (BBTools uses bgzip automatically for .gz output)
    echo "  Creating bgzipped FASTQ..."
        "$BBTOOLS_DIR/randomreadsmg.sh" \
            ref="$GENOME_FILE" \
            out="$bgz_fq" \
            reads="$num_reads" \
            length=150 \
            seed=42 
            # 2>/dev/null
        echo "    ✓ $bgz_fq ($(du -h "$bgz_fq" | cut -f1))"
}

# Generate all test file sets
for size in "${SIZES[@]}"; do
    generate_fastq_set "$size"
done

# Clean up temporary genome file
rm -f "$GENOME_FILE"

echo "Test data generated in: $DATA_DIR/"
echo ""
echo "Available test files:"
for size in "${SIZES[@]}"; do
    size_label="${size}m"
    echo "  ${size_label}:"
    echo "    Raw:      $DATA_DIR/${size_label}.fastq ($(du -h "$DATA_DIR/${size_label}.fastq" 2>/dev/null | cut -f1 || echo 'N/A'))"
    echo "    Gzipped:  $DATA_DIR/${size_label}.fastq.gz ($(du -h "$DATA_DIR/${size_label}.fastq.gz" 2>/dev/null | cut -f1 || echo 'N/A'))"
    echo "    Bgzipped: $DATA_DIR/${size_label}.fastq_bgzipped.gz ($(du -h "$DATA_DIR/${size_label}.fastq_bgzipped.gz" 2>/dev/null | cut -f1 || echo 'N/A'))"
done
echo ""
echo "Ready to run (cold - from pregenerated local files) benchmarks!"
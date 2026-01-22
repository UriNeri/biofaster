#!/bin/bash
# Comprehensive FASTQ Parser Benchmark Runner
# Tests BBTools vs needletail on both raw and gzipped FASTQ files
# with hot and Cold scenarios

set -e

# Determine script location for default BIOFASTER_ROOT
_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default settings
WARMUP_RUNS=1
MIN_RUNS=2
SKIP_COLD=false
SKIP_COMPRESSION_COMPARE=false
SIZES="0.001m,0.1m,1m,10m"
CUSTOM_ROOT=""
RAM_PATH="/tmp" #grep -E 'tmpfs|ramfs' /proc/mounts maybe?

# Parse arguments
usage() {
    cat << EOF
Usage: $0 [options]

Options:
    -w, --warmup <n>        Number of warmup runs for Hot (default: 1)
    -r, --runs <n>          Minimum number of benchmark runs (default: 2)
    -z, --sizes <sizes>     Comma-separated list of sizes to benchmark (e.g., "0.1m,1m,10m")
                            If not specified, all available sizes in test-data/ will be used
                            If a size doesn't exist, it will be generated automatically
    -s, --skip-cold         Skip Cold tests (uses vmtouch for cache management)
    -C, --skip-compression  Skip compression comparison tests (bgzip vs gzip)
    --root <path>           Set custom project root directory (default: script location)
    --ram-path <path>       Set custom RAM disk path (default: /tmp, alternative: /dev/shm)
    -h, --help              Show this help message

Cache Scenarios:
  - Hot: Files copied to RAM disk (default: /tmp, configurable) for minimal I/O overhead
  - Cold: Regular files with page cache evicted using vmtouch (graceful fallback to cp to RAM)

Note: Cold benchmarks use vmtouch to evict pages from cache before each run.
      If vmtouch fails, files are copied to RAM as fallback.

This script will benchmark:
  - By default: ALL test sizes found in test-data/ directory
  - With --sizes: Only the specified sizes
  - If test files don't exist, they will be generated automatically
  
  For each size:
    1. All tools on raw FASTQ (Hot - in RAM)
    2. All tools on gzipped FASTQ (Hot - in RAM)
    3. All tools on bgzip FASTQ (Hot - in RAM) - if not skipped with -C
    4. All tools on raw FASTQ (Cold - cache evicted) - if not skipped with -s
    5. All tools on gzipped FASTQ (Cold - cache evicted) - if not skipped with -s
    6. All tools on bgzip FASTQ (Cold - cache evicted) - if not skipped with -s or -C

Examples:
    $0                                      # Run with ALL available test sizes
    $0 --sizes 1m                           # Run with only 1m reads
    $0 -z "0.1m,1m,10m"                     # Run with 0.1m, 1m, and 10m reads
    $0 --sizes "0.5m,1m" -s                # Run 0.5m and 1m, skip cold tests
    $0 -z 5m                                # Run 5m (will generate if missing)
    $0 --root /path/to/biofaster            # Use custom project root

Results are saved to: \$BIOFASTER_ROOT/benchmark_results/benchmark_TIMESTAMP/
EOF
    exit 1
}

# Parse command-line arguments with getopt
TEMP=$(getopt -o w:r:z:sCh --long warmup:,runs:,sizes:,skip-cold,skip-compression,root:,ram-path:,help -n "$0" -- "$@")
if [ $? != 0 ]; then
    echo "Error parsing arguments. Use -h for help." >&2
    exit 1
fi

eval set -- "$TEMP"

while true; do
    case "$1" in
        -w|--warmup)
            WARMUP_RUNS="$2"
            shift 2
            ;;
        -r|--runs)
            MIN_RUNS="$2"
            shift 2
            ;;
        -z|--sizes)
            SIZES="$2"
            shift 2
            ;;
        -s|--skip-cold)
            SKIP_COLD=true
            shift
            ;;
        -C|--skip-compression)
            SKIP_COMPRESSION_COMPARE=true
            shift
            ;;
        --root)
            CUSTOM_ROOT="$2"
            shift 2
            ;;
        --ram-path)
            RAM_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Internal error!" >&2
            exit 1
            ;;
    esac
done

# Java setup - prefer local JRE if available
if [ -d "$BIOFASTER_ROOT/jre" ]; then
    export JAVA_HOME="$BIOFASTER_ROOT/jre"
    export PATH="$JAVA_HOME/bin:$PATH"
    echo "Using local JRE: $JAVA_HOME"
fi

# Set and export BIOFASTER_ROOT - this is the ONLY path variable tool scripts need
export BIOFASTER_ROOT="${CUSTOM_ROOT:-$_SCRIPT_DIR}"
# Set BBTools path - use environment variable or default to local BBTools directory
export BBTOOLS_PATH="${BBTOOLS_PATH:-$BIOFASTER_ROOT/BBTools/current/}"

# Derived paths (all relative to BIOFASTER_ROOT)
DATA_DIR="$BIOFASTER_ROOT/test-data"
RESULTS_DIR="$BIOFASTER_ROOT/benchmark_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_SUBDIR="$RESULTS_DIR/benchmark_$TIMESTAMP"
mkdir -p "$RESULT_SUBDIR"

# Discover available tools from tools/ directory
TOOLS_DIR="$BIOFASTER_ROOT/tools"
declare -A TOOLS
declare -A TOOL_COMMANDS

if [ -d "$TOOLS_DIR" ]; then
    echo ""
    echo "Discovering available tools..."
    for tool_script in "$TOOLS_DIR"/*.sh; do
        if [ -f "$tool_script" ] && [ -x "$tool_script" ]; then
            tool_name=$(basename "$tool_script" .sh)
            TOOLS["$tool_name"]="$tool_script"
            echo "  Found: $tool_name"
        fi
    done
    echo "Total tools available: ${#TOOLS[@]}"
else
    echo "Warning: tools/ directory not found at $TOOLS_DIR" >&2
    exit 1
fi

# Function to generate test files for a specific size if they don't exist
# Integrated from generate_static_input.sh
generate_test_files() {
    local size=$1
    local num_reads=$(echo "$size" | sed 's/m$//' | awk '{print $1 * 1000000}')
    
    echo "Generating test files for size: ${size}..."
    
    local genome_file="$DATA_DIR/ref_genome_temp.fa"
    local raw_fq="$DATA_DIR/${size}.fastq"
    local gz_fq="$DATA_DIR/${size}.fastq.gz"
    local bgz_fq="$DATA_DIR/${size}.fastq_bgzipped.gz"
    
    # Generate reference genome if needed
    if [ ! -f "$genome_file" ]; then
        echo "  Creating reference genome..."
        "$BIOFASTER_ROOT/BBTools/randomgenome.sh" len=100000 seed=42 out="$genome_file" 2>/dev/null
    fi
    
    # Generate raw FASTQ
    if [ ! -f "$raw_fq" ]; then
        echo "  Creating raw FASTQ (${num_reads} reads)..."
        "$BIOFASTER_ROOT/BBTools/randomreads.sh" \
            ref="$genome_file" \
            out="$raw_fq" \
            reads="$num_reads" \
            length=150 \
            seed=42 
            # 2>/dev/null
        echo "    ✓ $raw_fq ($(du -h "$raw_fq" | cut -f1))"
    fi
    
    # Generate (regular) gzipped FASTQ
    if [ ! -f "$gz_fq" ]; then
        echo "  Creating gzipped FASTQ..."
        if command -v pigz &> /dev/null; then
            pigz -k -c "$raw_fq" > "$gz_fq"
        else
            gzip -k -c "$raw_fq" > "$gz_fq"
        fi
        echo "    ✓ $gz_fq ($(du -h "$gz_fq" | cut -f1))"
    fi
    
    # Generate bgzipped FASTQ (using BBTools which outputs bgzip automatically)
    if [ ! -f "$bgz_fq" ]; then
        echo "  Creating bgzipped FASTQ..."
        "$BIOFASTER_ROOT/BBTools/randomreads.sh" \
            ref="$genome_file" \
            out="$bgz_fq" \
            reads="$num_reads" \
            length=150 \
            seed=42 
            # 2>/dev/null
        echo "    ✓ $bgz_fq ($(du -h "$bgz_fq" | cut -f1))"
    fi
    
    # Clean up temp genome
    rm -f "$genome_file"
}

# Function to generate all standard test files if they don't exist
# Based on generate_static_input.sh
generate_all_test_files() {
    echo "Checking for existing test files in: $DATA_DIR"
    
    # Standard sizes from the original generate_static_input.sh
    local standard_sizes=("0.1" "0.5" "1" "10" "30" "50" "70")
    
    for size_decimal in "${standard_sizes[@]}"; do
        local size_label="${size_decimal}m"
        local raw_fq="$DATA_DIR/${size_label}.fastq"
        
        # Only generate if the raw file doesn't exist
        if [ ! -f "$raw_fq" ]; then
            echo "Missing $size_label files, generating..."
            generate_test_files "$size_label"
        else
            echo "✓ $size_label files already exist"
        fi
    done
}

# Discover available test sizes or use specified SIZES
declare -a TEST_SIZES=()

if [ -n "$SIZES" ]; then
    # User specified sizes to benchmark (comma or space separated)
    echo "Using specified sizes: $SIZES"
    # Convert comma-separated to array, handle both comma and space separation
    IFS=', ' read -ra TEST_SIZES <<< "$SIZES"
    
    # Check if files exist for each size, generate if needed
    for size in "${TEST_SIZES[@]}"; do
        RAW_FQ="$DATA_DIR/${size}.fastq"
        if [ ! -f "$RAW_FQ" ]; then
            echo "Test files for size $size not found. Generating..."
            generate_test_files "$size"
        fi
    done
else
    # Auto-discover available test sizes from test-data directory
    echo "Auto-discovering test sizes from: $DATA_DIR"
    
    # Generate standard files if test-data is empty or missing key files
    if [ ! -d "$DATA_DIR" ] || [ -z "$(find "$DATA_DIR" -name "*.fastq" 2>/dev/null)" ]; then
        echo "No test files found. Generating standard test files..."
        mkdir -p "$DATA_DIR"
        generate_all_test_files
    fi
    
    # Discover all available .fastq files and extract size labels
    for fastq_file in "$DATA_DIR"/*.fastq; do
        if [ -f "$fastq_file" ]; then
            basename_file=$(basename "$fastq_file" .fastq)
            # Only include files that match the expected naming pattern (e.g., 1m.fastq)
            if [[ "$basename_file" =~ ^[0-9]+(\.[0-9]+)?m$ ]]; then
                TEST_SIZES+=("$basename_file")
            fi
        fi
    done
    
    # Sort sizes numerically
    IFS=$'\n' TEST_SIZES=($(sort -V <<< "${TEST_SIZES[*]}"))
    unset IFS
    
    if [ ${#TEST_SIZES[@]} -eq 0 ]; then
        echo "No valid test files found in $DATA_DIR"
        echo "Expected files like: 1m.fastq, 10m.fastq, etc."
        exit 1
    fi
    
    echo "Found ${#TEST_SIZES[@]} test sizes: ${TEST_SIZES[*]}"
fi



echo ""
echo "=========================================="
echo "FASTQ Parser Benchmark"
echo "=========================================="

# Capture system information
echo "Capturing system information..."
mkdir -p "$RESULT_SUBDIR"

cat > "$RESULT_SUBDIR/system_info.json" << EOF
{
  "os": "$(uname -o 2>/dev/null || uname -s)",
  "kernel": "$(uname -r)",
  "architecture": "$(uname -m)",
  "cpu": "$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d':' -f2 | xargs || sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "N/A")",
  "cpu_cores": "$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "N/A")",
  "cpu_threads": "$(grep -c processor /proc/cpuinfo 2>/dev/null || sysctl -n hw.logicalcpu 2>/dev/null || echo "N/A")",
  "cpu_frequency": "$(lscpu 2>/dev/null | grep 'CPU MHz' | awk '{print $3 " MHz"}' || sysctl -n hw.cpufrequency 2>/dev/null | awk '{print $1/1000000 " MHz"}' || echo "N/A")",
  "cpu_cache_l3": "$(lscpu 2>/dev/null | grep 'L3 cache' | awk '{print $3}' || sysctl -n hw.l3cachesize 2>/dev/null | awk '{print $1/1024/1024 " MiB"}' || echo "N/A")",
  "ram": "$(free -h 2>/dev/null | awk '/^Mem:/ {print $2}' || sysctl -n hw.memsize 2>/dev/null | awk '{print $1/1024/1024/1024 " GB"}' || echo "N/A")",
  "ram_total_bytes": "$(free -b 2>/dev/null | awk '/^Mem:/ {print $2}' || sysctl -n hw.memsize 2>/dev/null || echo "N/A")",
  "disk_device": "$(df . 2>/dev/null | tail -1 | awk '{print $1}')",
  "filesystem": "$(df -T . 2>/dev/null | tail -1 | awk '{print $2}' || df -h . | tail -1 | awk '{print "N/A"}')",
  "disk_total": "$(df -h . | tail -1 | awk '{print $2}')",
  "disk_available": "$(df -h . | tail -1 | awk '{print $4}')",
  "disk_used_percent": "$(df -h . | tail -1 | awk '{print $5}')",
  "disk_model": "$(lsblk -d -o name,model 2>/dev/null | grep -v 'NAME' | head -1 | awk '{$1=""; print $0}' | xargs || echo "N/A")",
  "python_version": "$(python3 --version 2>/dev/null | cut -d' ' -f2 || echo "N/A")",
  "python_path": "$(which python3 2>/dev/null || echo "N/A")",
  "hyperfine_version": "$(hyperfine --version 2>/dev/null | cut -d' ' -f2 || echo "N/A")",
  "java_version": "$(java -version 2>&1 | head -1 | cut -d'"' -f2 || echo "N/A")",
  "cache_drop_available": "$(sudo -n true 2>/dev/null && echo 'true' || echo 'false')",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "date_local": "$(date)"
}
EOF

echo "✅ System info saved to $RESULT_SUBDIR/system_info.json"
echo "Date: $(date)"
echo "Java version: $(java -version 2>&1 | head -1)"
echo "Test sizes to benchmark: ${TEST_SIZES[*]}"
echo "Warmup runs: $WARMUP_RUNS"
echo "Min benchmark runs: $MIN_RUNS"
echo "Results directory: $RESULT_SUBDIR"
echo "=========================================="
echo ""

# Function to run Hot benchmark
run_hot() {
    local file=$1
    local label=$2
    local json_output=$3
    
    echo ""
    echo "=========================================="
    echo "Hot Benchmark: $label"
    echo "=========================================="
    echo "Note: Copying file to RAM disk ($RAM_PATH) for minimal I/O overhead"
    
    local tmp_file="$RAM_PATH/benchmark_hot_$(basename "$file")"
    
    # Create output directory for capturing tool stdout
    local output_dir="${json_output%.json}_outputs"
    mkdir -p "$output_dir"
    
    # Copy file to RAM disk
    echo "Copying file to RAM disk ($RAM_PATH)..."
    cp "$file" "$tmp_file"
    
    # Build hyperfine command arguments from discovered tools (using tmp_file path)
    # Capture stdout to single file per tool (overwrites each iteration)
    local hyperfine_args=()
    
    echo "Commands to be benchmarked:"
    for tool_name in "${!TOOLS[@]}"; do
        local tool_script="${TOOLS[$tool_name]}"
        local output_file="$output_dir/${tool_name}.txt"
        local cmd="$tool_script $tmp_file > $output_file 2>&1"
        
        echo "  $tool_name: output --> $output_file"
        hyperfine_args+=(--command-name "$tool_name" "$cmd")
    done
    
    echo ""
    echo "Tool outputs will be saved to: $output_dir/"
    
    echo "Running benchmarks with $WARMUP_RUNS warmup runs and minimum $MIN_RUNS runs..."
    
    hyperfine \
        --warmup $WARMUP_RUNS \
        --min-runs $MIN_RUNS \
        --ignore-failure \
        --shell=bash \
        --prepare "rm -rf ref/ tmp/" \
        --conclude "rm -rf ref/" \
        --export-json "$json_output" \
        --export-markdown "${json_output%.json}.md" \
        "${hyperfine_args[@]}"
    
    # Clean up temp file after all benchmarks complete
    rm -f "$tmp_file"
    
    echo "Results saved to: $json_output"
    echo "Tool outputs saved to: $output_dir/"
}

# Function to run Cold benchmark using vmtouch for cache management
run_cold() {
    local file=$1
    local label=$2
    local json_output=$3
    
    echo ""
    echo "=========================================="
    echo "Cold Benchmark: $label"
    echo "=========================================="
    echo "Note: Using vmtouch to evict pages from cache (fallback to RAM copy)"
    
    # Create output directory for capturing tool stdout
    local output_dir="${json_output%.json}_outputs"
    mkdir -p "$output_dir"
    
    # Check if vmtouch is available and try to evict the file from cache
    local cache_method="none"
    local prepare_cmd="rm -rf ref/ tmp/"
    local ram_file=""
    
    if command -v vmtouch >/dev/null 2>&1; then
        # Try using vmtouch to evict the file from cache
        if vmtouch -t "$file" >/dev/null 2>&1 && vmtouch -e "$file" >/dev/null 2>&1; then
            cache_method="vmtouch"
            prepare_cmd="rm -rf ref/ tmp/ && vmtouch -e $file >/dev/null 2>&1"
            echo "✓ vmtouch available - pages will be evicted before each run"
        else
            cache_method="ram_fallback"
            ram_file="$RAM_PATH/cold_benchmark_$(basename "$file")_$$"
            prepare_cmd="rm -rf ref/ tmp/ $ram_file && cp $file $ram_file"
            echo "⚠ vmtouch failed - falling back to RAM copy method"
            echo "  File will be copied to RAM before each run: $ram_file"
        fi
    else
        cache_method="ram_fallback"
        ram_file="$RAM_PATH/cold_benchmark_$(basename "$file")_$$"
        prepare_cmd="rm -rf ref/ tmp/ $ram_file && cp $file $ram_file"
        echo "⚠ vmtouch not available - using RAM copy method"
        echo "  File will be copied to RAM before each run: $ram_file"
    fi
    
    # Log cache method to a sidecar file
    local status_file="${json_output%.json}_cache_status.txt"
    echo "cache_method=$cache_method" > "$status_file"
    echo "timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$status_file"
    echo "original_file=$file" >> "$status_file"
    if [ -n "$ram_file" ]; then
        echo "ram_file=$ram_file" >> "$status_file"
    fi
    
    # Determine which file path to use in the benchmarks
    local benchmark_file="$file"
    if [ "$cache_method" = "ram_fallback" ]; then
        benchmark_file="$ram_file"
    fi
    
    # Build hyperfine command arguments from discovered tools
    # Capture stdout to single file per tool (overwrites each iteration)
    local hyperfine_args=()
    
    echo ""
    echo "Commands to be benchmarked:"
    for tool_name in "${!TOOLS[@]}"; do
        local tool_script="${TOOLS[$tool_name]}"
        local output_file="$output_dir/${tool_name}.txt"
        local cmd="$tool_script $benchmark_file > $output_file 2>&1"
        
        echo "  $tool_name: output --> $output_file"
        hyperfine_args+=(--command-name "$tool_name" "$cmd")
    done
    echo ""
    echo "Tool outputs will be saved to: $output_dir/"
    
    # Add cleanup command if using RAM fallback
    local conclude_cmd="rm -rf ref/"
    if [ -n "$ram_file" ]; then
        conclude_cmd="rm -rf ref/ $ram_file"
    fi
    
    echo "Running benchmarks with 3 runs..."
    
    hyperfine \
        --runs 3 \
        --ignore-failure \
        --shell=bash \
        --prepare "$prepare_cmd" \
        --conclude "$conclude_cmd" \
        --export-json "$json_output" \
        --export-markdown "${json_output%.json}.md" \
        "${hyperfine_args[@]}"
    
    echo "Results saved to: $json_output"
    echo "Tool outputs saved to: $output_dir/"
    echo "Cache method: $cache_method (logged to $status_file)"
}



# Run benchmarks for each test size
for TEST_SIZE in "${TEST_SIZES[@]}"; do
    echo ""
    echo "######################################################################"
    echo "# Benchmarking test size: $TEST_SIZE"
    echo "######################################################################"
    echo ""
    
    # Define file paths for this size
    RAW_FQ="$DATA_DIR/${TEST_SIZE}.fastq"
    GZ_FQ="$DATA_DIR/${TEST_SIZE}.fastq.gz"
    BGZIP_FQ="$DATA_DIR/${TEST_SIZE}.fastq_bgzipped.gz"
    
    # Create size-specific subdirectory for results
    SIZE_RESULT_DIR="$RESULT_SUBDIR/${TEST_SIZE}"
    mkdir -p "$SIZE_RESULT_DIR"
    
    echo "Files for this size:"
    echo "  Raw:      $RAW_FQ ($(du -h "$RAW_FQ" | cut -f1))"
    echo "  Gzipped:  $GZ_FQ ($(du -h "$GZ_FQ" | cut -f1))"
    echo "  Bgzipped: $BGZIP_FQ ($(du -h "$BGZIP_FQ" | cut -f1))"
    echo ""
    
    # Run Hot benchmarks
    run_hot "$RAW_FQ" "Raw FASTQ ($TEST_SIZE)" "$SIZE_RESULT_DIR/hot_raw.json"
    run_hot "$GZ_FQ" "Gzipped FASTQ ($TEST_SIZE)" "$SIZE_RESULT_DIR/hot_gz.json"
    
    if [ "$SKIP_COMPRESSION_COMPARE" = false ] && [ -f "$BGZIP_FQ" ]; then
        run_hot "$BGZIP_FQ" "Bgzipped FASTQ ($TEST_SIZE)" "$SIZE_RESULT_DIR/hot_bgz.json"
    fi
    
    # Run Cold benchmarks
    if [ "$SKIP_COLD" = false ]; then
        run_cold "$RAW_FQ" "Raw FASTQ ($TEST_SIZE)" "$SIZE_RESULT_DIR/cold_raw.json"
        run_cold "$GZ_FQ" "Gzipped FASTQ ($TEST_SIZE)" "$SIZE_RESULT_DIR/cold_gz.json"
        
        if [ "$SKIP_COMPRESSION_COMPARE" = false ] && [ -f "$BGZIP_FQ" ]; then
            run_cold "$BGZIP_FQ" "Bgzipped FASTQ ($TEST_SIZE)" "$SIZE_RESULT_DIR/cold_bgz.json"
        fi
    else
        echo ""
        echo "Skipping Cold tests for $TEST_SIZE (use without -s to enable)"
    fi

done

# Create summary
echo ""
echo "=========================================="
echo "Benchmark Complete!"
echo "=========================================="
echo "All results saved to: $RESULT_SUBDIR"
echo ""
echo "Files created:"
ls -lh "$RESULT_SUBDIR"

# Create a summary report
SUMMARY_FILE="$RESULT_SUBDIR/SUMMARY.txt"
{
    echo "FASTQ Parser Benchmark Summary"
    echo "=============================="
    echo "Date: $(date)"
    echo "Host: $(hostname)"
    echo ""
    echo "Test Configuration:"
    echo "  Test sizes benchmarked: ${TEST_SIZES[*]}"
    echo "  Warmup runs: $WARMUP_RUNS"
    echo "  Benchmark runs: $MIN_RUNS"
    echo ""
    echo "File sizes:"
    for size in "${TEST_SIZES[@]}"; do
        echo "  $size:"
        echo "    Raw:      $(du -h "$DATA_DIR/${size}.fastq" 2>/dev/null | cut -f1 || echo 'N/A')"
        echo "    Gzipped:  $(du -h "$DATA_DIR/${size}.fastq.gz" 2>/dev/null | cut -f1 || echo 'N/A')"
        if [ "$SKIP_COMPRESSION_COMPARE" = false ]; then
            echo "    Bgzipped: $(du -h "$DATA_DIR/${size}.fastq_bgzipped.gz" 2>/dev/null | cut -f1 || echo 'N/A')"
        fi
    done
    echo ""
    echo "Benchmarks performed per size:"
    echo "  - Hot (raw FASTQ)"
    echo "  - Hot (gzipped FASTQ)"
    if [ "$SKIP_COMPRESSION_COMPARE" = false ]; then
        echo "  - Hot (bgzipped FASTQ)"
    fi
    if [ "$SKIP_COLD" = false ]; then
        echo "  - Cold (raw FASTQ) - cache evicted with vmtouch"
        echo "  - Cold (gzipped FASTQ) - cache evicted with vmtouch"
        if [ "$SKIP_COMPRESSION_COMPARE" = false ]; then
            echo "  - Cold (bgzipped FASTQ) - cache evicted with vmtouch"
        fi
    fi
    echo ""
    echo "Result directories:"
    find "$RESULT_SUBDIR" -type d | sed 's|^|  |'
    echo ""
    echo "Total result files: $(find "$RESULT_SUBDIR" -type f | wc -l)"
} > "$SUMMARY_FILE"

echo ""
cat "$SUMMARY_FILE"

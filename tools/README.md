# Tools Directory

This directory contains individual tool scripts for FASTQ parser benchmarking. Each tool is implemented as a standalone bash script that accepts a FASTQ file path as its first argument.

## How It Works

The `run_all_benchmarks.sh` script automatically discovers all `.sh` files in this directory and includes them in the benchmark suite. This makes it easy to add or remove tools without modifying the main benchmark script.

## Tool Script Format

Each tool script must:
1. Be a bash script with `.sh` extension
2. Be executable (`chmod +x toolname.sh`)
3. Accept the input FASTQ file path as `$1`
4. Execute the tool command with `exec` for proper signal handling
5. Include error checking for dependencies

### Template

```bash
#!/bin/bash
# tool-name: Brief description of the tool
# Args: $1 = input FASTQ file path

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

# Add any setup/dependency checks here
if [ ! -f "/path/to/tool" ]; then
    echo "Error: Tool not found" >&2
    exit 1
fi

# Execute the tool with the input file
# Use 'exec' to replace the shell process with the tool process
exec /path/to/tool "$1"
```

## Adding a New Tool

1. Create a new `.sh` file in this directory (e.g., `my-parser.sh`)
2. Follow the template above
3. Make it executable: `chmod +x my-parser.sh`
4. The tool will automatically be included in the next benchmark run

**Example**: Adding a C implementation from biofast

```bash
#!/bin/bash
# biofast-c: C implementation using kseq.h
# Args: $1 = input FASTQ file path

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
BIN="$SCRIPT_DIR/biofast-reference/fqcnt/fqcnt_c1_kseq"

if [ ! -f "$BIN" ]; then
    echo "Error: biofast C binary not found at $BIN" >&2
    echo "Compile it first from biofast-reference/fqcnt/" >&2
    exit 1
fi

exec "$BIN" "$1"
```

## Removing a Tool

Simply delete or rename the `.sh` file (e.g., rename to `.sh.disabled`). The tool will be excluded from future benchmarks.

## Current Tools

### Original Implementations
- **needletail-rust.sh** - Fast Rust-based FASTQ parser with SIMD base counting
- **needletail-python.sh** - Python bindings to needletail (tests FFI overhead)
- **bbtools-streamer.sh** - BBTools StreamerWrapper with SIMD and multi-threading
- **fastqscan.sh** - BBTools' ultra-fast parser (skips validation)

### Biofast Python Implementations
- **biofast-py1-4l.sh** - Pure Python (4-line FASTQ parser, no dependencies)
- **biofast-py2-rfq.sh** - Pure Python with readfq function (handles FASTA/FASTQ, no dependencies)
- **biofast-py3-mappy.sh** - Python with mappy (minimap2 bindings) - requires `pixi add mappy --pypi`
- **biofast-py4-bpitr.sh** - Python with BioPython FastqGeneralIterator - requires `pixi add biopython`
- **biofast-py5-bp.sh** - Python with BioPython SeqIO.parse - requires `pixi add biopython`
- **biofast-py6-pyfx.sh** - Python with pyfastx - requires `pixi add pyfastx`
- **biofast-py7-pysam.sh** - Python with pysam (samtools bindings) - requires `pixi add pysam`
- **biofast-py8-fx.sh** - Python with fastx - requires `pixi add fastx-py --pypi`

## Environment Variables

Some tools use environment variables for configuration:

- `BBTOOLS_PATH` - Path to BBTools installation (default: `./BBTools/current/`)
- `JAVA_HOME` - Java installation path (auto-detected if not set)

## Notes

- Tool names in the benchmark results are derived from the script filename (without `.sh`)
- Scripts should handle their own error checking and dependency validation
- Use `exec` to ensure proper signal handling and clean process management
- The benchmark script exports `BBTOOLS_PATH` for tools that need it

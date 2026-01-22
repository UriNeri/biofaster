# paraseq_filt

Parallel FASTA/FASTQ filtering tool with a CLI and Python bindings.  
Uses `paraseq` crate

## NOTE
This is a crude, partially vibe coded and hastily made attempt. It's mostly to add a comparison point in biofaster benchmark for muti-threaded FASTA/FASTQ parsing and filtering. The `filt` is cause we wondered if we can use it to filter sequences by headers.

## Installation

**Using pixi (recommended):**
```bash
pixi run build-cli      # Rust CLI
pixi run build-python   # Python bindings
```

**Without pixi:**
```bash
cargo build --release           # CLI: target/release/paraseq_filt
pip install maturin && maturin develop --release  # Python
```

## Usage

### CLI
```bash
# Count mode (for benchmarking)
paraseq_filt --count -i input.fasta

# Filter mode
paraseq_filt -i input.fasta -o output.fasta -H headers.txt
paraseq_filt -i input.fasta -o output.fasta -H "seq1,seq2,seq3"
paraseq_filt -i input.fasta -o output.fasta -H headers.txt --invert -t 8
```


## Options

```
-i, --input <FILE>      Input file (supports .gz)
-o, --output <FILE>     Output file (required for filter mode)
-H, --headers <LIST>    Comma-separated IDs or file path (required for filter mode)
-v, --invert            Exclude matching sequences
-t, --threads <N>       Thread count (default: CPU count)
-c, --count             Count mode: just count reads and bases
```

## Python API Reference
see [`PYTHON_GUIDE.md`](PYTHON_GUIDE.md) for details.
```python
import paraseq_filt

# Filter sequences
filter_fasta_by_headers(
    input_file: str | Path,
    output_file: str | Path,
    headers: list[str] | str | Path,
    invert: bool = False,
    num_threads: int | None = None,
) -> tuple[int, int]  # (processed, written)

# Count reads and bases
count_records(
    input_file: str | Path,
    num_threads: int | None = None,
) -> tuple[int, int]  # (num_reads, num_bases)

# Parse records as (id, sequence, quality) tuples
# Quality is None for FASTA, contains scores for FASTQ
parse_records(input_file: str | Path) -> list[tuple[str, str, str | None]]

load_headers_from_file(file_path: str | Path) -> list[str]
# example:
processed, written = paraseq_filt.filter_fasta_by_headers(
    "input.fasta",
    "output.fasta",
    ["seq1", "seq2", "seq3"],
    num_threads=8
)

# Or from file
processed, written = paraseq_filt.filter_fasta_by_headers(
    "input.fasta.gz",
    "output.fasta",
    "headers.txt",
    invert=True
)

```

## Benchmarking
This is meant to be measured in [biofaster](https://github.com/UriNeri/biofaster) (only streaming and base/read cunting). 
For benchmarking the `filt` options see `benchmarks/benchmark_seqkit.sh`.  
For a more detailed benchmarking see [Noam Teyssier blog post](https://noamteyssier.github.io/2025-02-03/) and benchmark repo in:  
https://github.com/noamteyssier/paraseq_benchmark  

## Testing

```bash
pixi run test           # All tests
pixi run test-rust      # CLI tests
bash tests/test_count.sh  # Count mode tests
pixi run test-python    # Python tests
```

Or manually: `bash tests/test.sh` and `python tests/test_python.py`


## License
MIT (same as the license of the paraseq crate)


# Python Bindings

Python bindings for paraseq_filt using PyO3.

## Installation

```bash
pixi run build-python
# or: pip install maturin && maturin develop --release
```

## Type Support

Includes `.pyi` stubs and `py.typed` marker for IDE autocomplete and type checking (mypy, pylance, pyright).

## API

### `filter_fasta_by_headers()`
```python
def filter_fasta_by_headers(
    input_file: str | Path,
    output_file: str | Path,
    headers: list[str] | str | Path,
    invert: bool = False,
    num_threads: int | None = None,
) -> tuple[int, int]  # (processed, written)
```

**Parameters:**
- `input_file`: Input file path (supports .gz)
- `output_file`: Output file path
- `headers`: List of IDs or path to file (one ID per line)
- `invert`: Exclude instead of include matches
- `num_threads`: Thread count (default: CPU count)

**Examples:**
```python
import paraseq_filt

# With list
processed, written = paraseq_filt.filter_fasta_by_headers(
    "input.fasta", "output.fasta", ["seq1", "seq2"]
)

# From file
processed, written = paraseq_filt.filter_fasta_by_headers(
    "input.fasta.gz", "output.fasta", "headers.txt", num_threads=8
)

# Invert
processed, written = paraseq_filt.filter_fasta_by_headers(
    "input.fasta", "output.fasta", ["seq1"], invert=True
)
```

### `load_headers_from_file()`
```python
def load_headers_from_file(file_path: str | Path) -> list[str]
```

Loads sequence IDs from file (one per line).

### `count_records()`
```python
def count_records(
    input_file: str | Path,
    num_threads: int | None = None,
) -> tuple[int, int]  # (num_reads, num_bases)
```

**Parameters:**
- `input_file`: Input file path (supports .gz)
- `num_threads`: Thread count (default: CPU count)

**Examples:**
```python
import paraseq_filt

# Count sequences and bases
num_reads, num_bases = paraseq_filt.count_records("input.fasta.gz")
print(f"{num_reads}\t{num_bases}")

# Use specific thread count
num_reads, num_bases = paraseq_filt.count_records("input.fastq", num_threads=4)
```

### `parse_records()`
```python
def parse_records(input_file: str | Path) -> list[tuple[str, str, str | None]]
```

**Parameters:**
- `input_file`: Input file path (supports .gz)

**Returns:** List of (id, sequence, quality) tuples. Quality is None for FASTA files.

**Examples:**
```python
import paraseq_filt

# FASTA file (quality will be None)
for seq_id, sequence, qual in paraseq_filt.parse_records("input.fasta"):
    print(f">{seq_id}")
    print(sequence)

# FASTQ file (quality contains scores)
for seq_id, sequence, qual in paraseq_filt.parse_records("input.fastq"):
    print(f"@{seq_id}")
    print(sequence)
    if qual:
        print("+")
        print(qual)

# Get all records at once
records = paraseq_filt.parse_records("input.fastq.gz")
print(f"Loaded {len(records)} sequences")
```

## Testing

```bash
pixi run test-python
```

## Examples

### Batch Processing
```python
from pathlib import Path
import paraseq_filt

headers = paraseq_filt.load_headers_from_file("headers.txt")

for fasta in Path("input/").glob("*.fasta*"):
    processed, written = paraseq_filt.filter_fasta_by_headers(
        str(fasta), f"output/{fasta.name}", headers, num_threads=8
    )
    print(f"{fasta.name}: {written}/{processed}")
```

# Biofaster Integration

Integration guide for adding `paraseq_filt` to the [biofaster](https://github.com/UriNeri/biofaster) benchmarking suite.

## Quick Integration

1. Copy the tool wrapper:
```bash
cp tools/paraseq-filt.sh /path/to/biofaster/tools/
chmod +x /path/to/biofaster/tools/paraseq-filt.sh
```

2. Build the binary:
```bash
# In this directory
pixi run build-cli
# or: cargo build --release
```

3. Copy binary to biofaster:
```bash
cp target/release/paraseq_filt /path/to/biofaster/target/release/
```

4. Run biofaster benchmarks:
```bash
cd /path/to/biofaster
./run_all_benchmarks.sh
```

## What Gets Benchmarked

The tool wrapper runs paraseq_filt in "count mode" (`--count`) which counts reads and bases without any filtering overhead. This tests pure parallel parsing performance comparable to other FASTQ parsers in biofaster.

The benchmark measures:
- Parallel FASTA/FASTQ parsing with paraseq crate
- Multi-threaded processing across CPU cores
- Gzipped file handling
- Memory-efficient streaming
- Base counting performance

## Expected Performance

Based on paraseq's parallel architecture:
- Should outperform single-threaded Python parsers
- Comparable to needletail-rust (both use Rust + parallel processing)
- May be slightly slower than needletail due to filtering overhead
- Benefits from multiple CPU cores

## Build Integration

Add to biofaster's `get_stuff.sh`:

```bash
# Compile paraseq_filt
echo "Compiling paraseq_filt..."
if [ -d "paraseq_filt" ]; then
    cd paraseq_filt
    cargo build --release
    cd ..
else
    echo "Warning: paraseq_filt not found. Clone from repo."
fi
```



## Notes

- paraseq_filt is designed for FASTA filtering, but handles FASTQ
- The wrapper adapts it to the biofast counting interface
- For pure FASTQ parsing, needletail may be more optimized
- paraseq_filt excels at filtering large files with many CPUs
